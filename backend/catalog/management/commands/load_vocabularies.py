import json
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

# Maps canonical JSON file stem -> (app_label, model_name)
# Must stay aligned with spec repo's scripts/build-vocabularies.js DJANGO_MODELS
VOCAB_MAP = {
    "subjects": ("catalog", "Subject"),
    "genres": ("catalog", "Genre"),
    "rights_statements": ("catalog", "RightsStatement"),
    "agent_kinds": ("agents", "AgentKind"),
    "agent_roles": ("agents", "AgentRole"),
    "repo_kinds": ("repositories", "RepoKind"),
    "holding_access_statuses": ("holdings", "AccessStatus"),
    "holding_distro_statuses": ("holdings", "DistroStatus"),
}


class Command(BaseCommand):
    help = "Load controlled vocabularies from canonical JSON files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--vocab-dir",
            default=settings.VOCAB_CANONICAL_DIR,
            help="Path to canonical vocabulary JSON directory",
        )
        parser.add_argument(
            "--vocab",
            choices=list(VOCAB_MAP.keys()),
            help="Load only a specific vocabulary",
        )

    def handle(self, *args, **options):
        vocab_dir = Path(options["vocab_dir"])
        if not vocab_dir.is_dir():
            self.stderr.write(self.style.ERROR(f"Directory not found: {vocab_dir}"))
            return

        vocabs_to_load = (
            {options["vocab"]: VOCAB_MAP[options["vocab"]]}
            if options["vocab"]
            else VOCAB_MAP
        )

        for filename, (app_label, model_name) in vocabs_to_load.items():
            json_path = vocab_dir / f"{filename}.json"
            if not json_path.exists():
                self.stderr.write(self.style.WARNING(f"Skipping {filename}: file not found"))
                continue

            with open(json_path) as f:
                data = json.load(f)

            Model = apps.get_model(app_label, model_name)
            terms = data.get("terms", [])

            created_count = 0
            updated_count = 0

            for term in terms:
                defaults = {"label": term["label"]}
                # Add extra fields for models that have them (e.g. RightsStatement)
                if hasattr(Model, "uri"):
                    defaults["uri"] = term.get("uri", "")
                if hasattr(Model, "description"):
                    defaults["description"] = term.get("description", "")

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
                    f"{filename}: {created_count} created, {updated_count} updated "
                    f"({len(terms)} total)"
                )
            )
