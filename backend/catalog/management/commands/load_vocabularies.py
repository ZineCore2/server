import json
from pathlib import Path

import requests
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# Extra fields to check on vocabulary models beyond code/label.
# Maps model attribute name -> canonical JSON term key.
_EXTRA_FIELD_MAP = {
    "uri": "uri",
    "description": "description",
    "lookup_uri": "lookup_uri",
    "info_uri": "info_uri",
    "owner_uri": "owner_uri",
    "applicable_to": "applicable_to",
    "base_uri": "base_uri",
    "category": "category",
    "icon": "icon",
}

# Vocabularies available from zinecore.org API (excluding languages and countries)
API_VOCABS = [
    "subjects",
    "genres",
    "rights_statements",
    "agent_kinds",
    "agent_roles",
    "repo_kinds",
    "holding_access_statuses",
    "holding_distro_statuses",
    "external_id_systems",
    "external_uri_types",
]

# Maps canonical JSON file stem -> (app_label, model_name)
# Must stay aligned with spec repo's scripts/build-vocabularies.js DJANGO_MODELS
VOCAB_MAP = {
    "subjects": ("catalog", "Subject"),
    "genres": ("catalog", "Genre"),
    "rights_statements": ("catalog", "RightsStatement"),
    "languages": ("catalog", "Language"),
    "agent_kinds": ("agents", "AgentKind"),
    "agent_roles": ("agents", "AgentRole"),
    "repo_kinds": ("repositories", "RepoKind"),
    "holding_access_statuses": ("holdings", "AccessStatus"),
    "holding_distro_statuses": ("holdings", "DistroStatus"),
    "external_id_systems": ("core", "ExternalIdSystem"),
    "external_uri_types": ("core", "ExternalUriType"),
}


class Command(BaseCommand):
    help = "Load controlled vocabularies from zinecore.org API or local JSON files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--vocab",
            choices=list(VOCAB_MAP.keys()),
            help="Load only a specific vocabulary",
        )
        parser.add_argument(
            "--local",
            action="store_true",
            help="Load from local spec/vocabularies/canonical/ directory instead of API",
        )
        parser.add_argument(
            "--vocab-dir",
            default=settings.VOCAB_CANONICAL_DIR,
            help="Path to canonical vocabulary JSON directory (only used with --local)",
        )
        parser.add_argument(
            "--api-url",
            default="https://zinecore.org/api/vocabularies",
            help="Base URL for vocabulary API",
        )

    def handle(self, *args, **options):
        use_local = options["local"]
        api_url = options["api_url"]
        vocab_dir = Path(options["vocab_dir"])

        # Determine which vocabularies to load
        vocabs_to_load = (
            {options["vocab"]: VOCAB_MAP[options["vocab"]]}
            if options["vocab"]
            else VOCAB_MAP
        )

        # Filter out languages when using API (has dedicated command)
        # Geographic places are loaded separately via load_geonames
        if not use_local:
            vocabs_to_load = {
                name: model_info
                for name, model_info in vocabs_to_load.items()
                if name in API_VOCABS
            }
            if not vocabs_to_load:
                self.stderr.write(
                    self.style.WARNING(
                        "Languages should be loaded with a dedicated command:\n"
                        "  ./manage.py load_languages\n"
                        "Geographic places are loaded separately:\n"
                        "  ./manage.py load_geonames"
                    )
                )
                return

        success_count = 0
        failure_count = 0

        for filename, (app_label, model_name) in vocabs_to_load.items():
            if use_local:
                success = self._load_from_local(filename, app_label, model_name, vocab_dir)
            else:
                success = self._load_from_api(filename, app_label, model_name, api_url)

            if success:
                success_count += 1
            else:
                failure_count += 1
                self.stderr.write(
                    self.style.WARNING(f"Failed to load {filename}")
                )

        # Raise error if all vocabularies failed to load
        if failure_count > 0 and success_count == 0:
            raise CommandError(
                f"Failed to load all {failure_count} vocabularies. "
                "Check network connection and API availability."
            )

    def _load_from_api(self, vocab_name: str, app_label: str, model_name: str, base_url: str) -> bool:
        """Load vocabulary from zinecore.org API."""
        url = f"{base_url}/{vocab_name}"
        self.stdout.write(f"Fetching {vocab_name} from {url}...")

        try:
            response = requests.get(
                url,
                headers={"Accept": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Failed to fetch {vocab_name}: {e}"))
            return False

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"Failed to parse JSON for {vocab_name}: {e}"))
            return False

        return self._process_vocabulary_data(vocab_name, app_label, model_name, data)

    def _load_from_local(self, filename: str, app_label: str, model_name: str, vocab_dir: Path) -> bool:
        """Load vocabulary from local JSON file."""
        json_path = vocab_dir / f"{filename}.json"

        if not json_path.exists():
            self.stderr.write(self.style.WARNING(f"File not found: {json_path}"))
            return False

        self.stdout.write(f"Loading {filename} from {json_path}...")

        try:
            with open(json_path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            self.stderr.write(self.style.ERROR(f"Failed to read {filename}: {e}"))
            return False

        return self._process_vocabulary_data(filename, app_label, model_name, data)

    def _process_vocabulary_data(self, vocab_name: str, app_label: str, model_name: str, data: dict) -> bool:
        """Process and save vocabulary data to database."""
        Model = apps.get_model(app_label, model_name)
        terms = data.get("terms", [])

        if not terms:
            self.stderr.write(self.style.WARNING(f"No terms found in {vocab_name}"))
            return False

        # Pre-resolve authority_scope GeoPlaces if the model has that field
        has_authority_scope = hasattr(Model, "authority_scope")
        geo_cache: dict[str, object] = {}
        if has_authority_scope:
            GeoPlace = apps.get_model("geography", "GeoPlace")
            country_codes = {
                t.get("authority_scope_country_code")
                for t in terms
                if t.get("authority_scope_country_code")
            }
            for cc in country_codes:
                try:
                    geo_cache[cc] = GeoPlace.objects.get(
                        country_code=cc, feature_code="PCLI"
                    )
                except GeoPlace.DoesNotExist:
                    self.stderr.write(
                        self.style.WARNING(
                            f"GeoPlace country not found for code '{cc}'"
                        )
                    )

        created_count = 0
        updated_count = 0

        for term in terms:
            defaults = {"label": term["label"]}

            # Add extra fields for models that have them
            for model_attr, json_key in _EXTRA_FIELD_MAP.items():
                if hasattr(Model, model_attr):
                    defaults[model_attr] = term.get(json_key, "")

            # Resolve authority_scope FK from country code
            if has_authority_scope:
                cc = term.get("authority_scope_country_code")
                defaults["authority_scope"] = geo_cache.get(cc) if cc else None

            _, created = Model.objects.update_or_create(
                code=term["code"],
                defaults=defaults,
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{vocab_name}: {created_count} created, {updated_count} updated "
                f"({len(terms)} total)"
            )
        )
        return True
