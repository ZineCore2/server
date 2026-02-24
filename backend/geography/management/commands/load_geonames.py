import io
import zipfile

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from pathlib import Path

from geography.models import GeoPlace

GEONAMES_BASE = "https://download.geonames.org/export/dump"
COUNTRY_INFO_URL = f"{GEONAMES_BASE}/countryInfo.txt"
ADMIN1_URL = f"{GEONAMES_BASE}/admin1CodesASCII.txt"
CITIES_URL = f"{GEONAMES_BASE}/cities15000.zip"

# countryInfo.txt column indices
CI_ISO = 0
CI_NAME = 4
CI_POPULATION = 7
CI_CONTINENT = 8
CI_GEONAMEID = 16

# admin1CodesASCII.txt column indices
A1_CODE = 0  # Format: "CC.ADM1"
A1_NAME = 1
A1_ASCII = 2
A1_GEONAMEID = 3

# cities15000.txt (standard geonames table) column indices
GN_ID = 0
GN_NAME = 1
GN_ASCII = 2
GN_LAT = 4
GN_LON = 5
GN_FCLASS = 6
GN_FCODE = 7
GN_CC = 8
GN_ADM1 = 10
GN_POP = 14


class Command(BaseCommand):
    help = "Load geographic places from GeoNames dump files (countries, admin1, cities15000)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--local-dir",
            type=str,
            default=None,
            help="Load from pre-downloaded files in this directory instead of fetching from the web.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show counts without saving to database.",
        )

    def handle(self, *args, **options):
        local_dir = Path(options["local_dir"]) if options["local_dir"] else None
        dry_run = options["dry_run"]

        # Phase 1: Countries
        self.stdout.write("Loading countries...")
        country_lines = self._get_lines(
            COUNTRY_INFO_URL, local_dir, "countryInfo.txt"
        )
        countries = self._parse_countries(country_lines)
        self.stdout.write(f"  Parsed {len(countries)} countries")

        # Phase 2: ADM1
        self.stdout.write("Loading admin1 divisions...")
        admin1_lines = self._get_lines(
            ADMIN1_URL, local_dir, "admin1CodesASCII.txt"
        )
        admin1s = self._parse_admin1(admin1_lines, countries)
        self.stdout.write(f"  Parsed {len(admin1s)} admin1 divisions")

        # Phase 3: Cities
        self.stdout.write("Loading cities (pop > 15000)...")
        city_lines = self._get_city_lines(local_dir)
        cities = self._parse_cities(city_lines, countries, admin1s)
        self.stdout.write(f"  Parsed {len(cities)} cities")

        total = len(countries) + len(admin1s) + len(cities)

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry run: {len(countries)} countries, {len(admin1s)} admin1, "
                    f"{len(cities)} cities ({total} total)"
                )
            )
            return

        self.stdout.write("Writing to database...")
        with transaction.atomic():
            GeoPlace.objects.all().delete()

            # Insert countries first (no parent)
            country_objs = GeoPlace.objects.bulk_create(
                countries.values(), batch_size=500
            )
            # Build lookup: country_code -> saved GeoPlace instance
            country_by_code = {obj.country_code: obj for obj in country_objs}

            # Set parent on admin1 objects now that countries have PKs
            for obj in admin1s.values():
                parent = country_by_code.get(obj.country_code)
                if parent:
                    obj.parent = parent

            admin1_objs = GeoPlace.objects.bulk_create(
                admin1s.values(), batch_size=2000
            )
            # Build lookup: (country_code, admin1_code) -> saved GeoPlace
            admin1_by_key = {
                (obj.country_code, obj.admin1_code): obj for obj in admin1_objs
            }

            # Set parent on city objects
            for obj in cities:
                parent = admin1_by_key.get((obj.country_code, obj.admin1_code))
                if not parent:
                    parent = country_by_code.get(obj.country_code)
                obj.parent = parent

            GeoPlace.objects.bulk_create(cities, batch_size=2000)

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded GeoNames: {len(countries)} countries, {len(admin1s)} admin1, "
                f"{len(cities)} cities ({total} total)"
            )
        )

    def _get_lines(self, url, local_dir, filename):
        """Fetch lines from URL or local file."""
        if local_dir:
            path = local_dir / filename
            if not path.exists():
                raise CommandError(f"File not found: {path}")
            return path.read_text(encoding="utf-8").splitlines()

        self.stdout.write(f"  Downloading {url}...")
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        return response.text.splitlines()

    def _get_city_lines(self, local_dir):
        """Get city lines from zip (download or local)."""
        if local_dir:
            # Try unzipped file first, then zip
            txt_path = local_dir / "cities15000.txt"
            if txt_path.exists():
                return txt_path.read_text(encoding="utf-8").splitlines()
            zip_path = local_dir / "cities15000.zip"
            if not zip_path.exists():
                raise CommandError(f"Neither cities15000.txt nor cities15000.zip found in {local_dir}")
            with zipfile.ZipFile(zip_path) as zf:
                with zf.open("cities15000.txt") as f:
                    return f.read().decode("utf-8").splitlines()

        self.stdout.write(f"  Downloading {CITIES_URL}...")
        response = requests.get(CITIES_URL, timeout=300)
        response.raise_for_status()
        buf = io.BytesIO(response.content)
        with zipfile.ZipFile(buf) as zf:
            with zf.open("cities15000.txt") as f:
                return f.read().decode("utf-8").splitlines()

    def _parse_countries(self, lines):
        """Parse countryInfo.txt -> dict of country_code -> GeoPlace."""
        countries = {}
        for line in lines:
            if not line or line.startswith("#"):
                continue
            cols = line.split("\t")
            if len(cols) <= CI_GEONAMEID:
                continue
            try:
                geoname_id = int(cols[CI_GEONAMEID])
            except (ValueError, IndexError):
                continue

            code = cols[CI_ISO].strip()
            if not code:
                continue

            countries[code] = GeoPlace(
                geoname_id=geoname_id,
                name=cols[CI_NAME].strip(),
                ascii_name=cols[CI_NAME].strip(),
                feature_class="A",
                feature_code="PCLI",
                country_code=code,
                admin1_code="",
                continent_code=cols[CI_CONTINENT].strip() if len(cols) > CI_CONTINENT else "",
                latitude=None,
                longitude=None,
                population=int(cols[CI_POPULATION]) if cols[CI_POPULATION].strip() else 0,
                parent=None,
            )
        return countries

    def _parse_admin1(self, lines, countries):
        """Parse admin1CodesASCII.txt -> dict of (cc, adm1) -> GeoPlace."""
        admin1s = {}
        for line in lines:
            if not line or line.startswith("#"):
                continue
            cols = line.split("\t")
            if len(cols) < 4:
                continue

            code_parts = cols[A1_CODE].split(".")
            if len(code_parts) != 2:
                continue
            cc, adm1 = code_parts

            # Skip if country not in our dataset
            if cc not in countries:
                continue

            try:
                geoname_id = int(cols[A1_GEONAMEID])
            except (ValueError, IndexError):
                continue

            country = countries[cc]
            admin1s[(cc, adm1)] = GeoPlace(
                geoname_id=geoname_id,
                name=cols[A1_NAME].strip(),
                ascii_name=cols[A1_ASCII].strip() if len(cols) > A1_ASCII else "",
                feature_class="A",
                feature_code="ADM1",
                country_code=cc,
                admin1_code=adm1,
                continent_code=country.continent_code,
                latitude=None,
                longitude=None,
                population=0,
                parent=None,  # Will be set after countries are saved
            )
        return admin1s

    def _parse_cities(self, lines, countries, admin1s):
        """Parse cities15000.txt -> list of GeoPlace."""
        cities = []
        for line in lines:
            if not line or line.startswith("#"):
                continue
            cols = line.split("\t")
            if len(cols) < 15:
                continue

            try:
                geoname_id = int(cols[GN_ID])
                lat = float(cols[GN_LAT]) if cols[GN_LAT] else None
                lon = float(cols[GN_LON]) if cols[GN_LON] else None
                pop = int(cols[GN_POP]) if cols[GN_POP] else 0
            except (ValueError, IndexError):
                continue

            cc = cols[GN_CC].strip()
            adm1 = cols[GN_ADM1].strip()
            country = countries.get(cc)
            continent = country.continent_code if country else ""

            cities.append(GeoPlace(
                geoname_id=geoname_id,
                name=cols[GN_NAME].strip(),
                ascii_name=cols[GN_ASCII].strip(),
                feature_class=cols[GN_FCLASS].strip(),
                feature_code=cols[GN_FCODE].strip(),
                country_code=cc,
                admin1_code=adm1,
                continent_code=continent,
                latitude=lat,
                longitude=lon,
                population=pop,
                parent=None,  # Will be set after admin1s are saved
            ))
        return cities
