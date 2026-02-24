import json

import requests
from django.core.management.base import BaseCommand, CommandError

from catalog.models import Language

LOC_ISO639_1_URL = "http://id.loc.gov/vocabulary/iso639-1.json"
MADS_CODE_KEY = "http://www.loc.gov/mads/rdf/v1#code"
MADS_LABEL_KEY = "http://www.loc.gov/mads/rdf/v1#authoritativeLabel"


class Command(BaseCommand):
    help = "Load ISO 639-1 language codes from Library of Congress vocabulary"

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            default=LOC_ISO639_1_URL,
            help="URL to fetch ISO 639-1 vocabulary JSON",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be loaded without saving to database",
        )

    def handle(self, *args, **options):
        url = options["url"]
        dry_run = options["dry_run"]

        self.stdout.write(f"Fetching ISO 639-1 vocabulary from {url}...")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise CommandError(f"Failed to fetch vocabulary: {e}")

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise CommandError(f"Failed to parse JSON: {e}")

        if not isinstance(data, list):
            raise CommandError("Expected JSON array at top level")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for entry in data:
            # Skip entries without required fields
            if not isinstance(entry, dict):
                continue

            code_value = entry.get(MADS_CODE_KEY)
            labels = entry.get(MADS_LABEL_KEY, [])

            # Skip if no code or labels
            if not code_value or not labels:
                skipped_count += 1
                continue

            # Extract code (may be wrapped in a dict)
            if isinstance(code_value, dict):
                code = code_value.get("@value", "")
            elif isinstance(code_value, list) and len(code_value) > 0:
                code = code_value[0].get("@value", "") if isinstance(code_value[0], dict) else str(code_value[0])
            else:
                code = str(code_value)

            if not code:
                skipped_count += 1
                continue

            # Extract English label (prefer English, fallback to first available)
            label = None
            for label_obj in labels:
                if isinstance(label_obj, dict):
                    lang = label_obj.get("@language", "")
                    value = label_obj.get("@value", "")
                    if lang == "en" and value:
                        label = value
                        break
                    elif not label and value:
                        label = value

            if not label:
                self.stdout.write(
                    self.style.WARNING(f"Skipping {code}: no label found")
                )
                skipped_count += 1
                continue

            if dry_run:
                self.stdout.write(f"Would load: {code} -> {label}")
                created_count += 1
                continue

            # Create or update the Language model
            _, created = Language.objects.update_or_create(
                code=code,
                defaults={"label": label},
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry run: would create/update {created_count} languages, "
                    f"skipped {skipped_count}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Loaded ISO 639-1 languages: {created_count} created, "
                    f"{updated_count} updated, {skipped_count} skipped "
                    f"({created_count + updated_count} total)"
                )
            )
