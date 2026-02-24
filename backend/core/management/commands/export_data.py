import sys
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand

# Models containing user-created data (not pre-loaded vocabularies or geography).
# Order matters: agents before zines (through models reference agents).
DATA_MODELS = [
    "agents.Agent",
    "repositories.Repository",
    "core.ExternalIdentifier",
    "core.ExternalUri",
    "catalog.Zine",
    "catalog.ZineCreator",
    "catalog.ZineContributor",
    "catalog.ZinePublisher",
    "holdings.Holding",
]


class Command(BaseCommand):
    help = (
        "Export user-created data (agents, repositories, zines, holdings) "
        "as a JSON fixture. Excludes pre-loaded vocabularies and geography."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--output",
            default=None,
            help="Output file path (default: stdout).",
        )
        parser.add_argument(
            "--indent",
            type=int,
            default=2,
            help="JSON indentation level (default: 2).",
        )

    def handle(self, *args, **options):
        output_path = options["output"]
        indent = options["indent"]

        kwargs = {
            "natural_foreign": True,
            "indent": indent,
        }

        if output_path:
            kwargs["output"] = output_path
            call_command("dumpdata", *DATA_MODELS, **kwargs)
            count_msg = Path(output_path).stat().st_size
            self.stdout.write(
                self.style.SUCCESS(
                    f"Exported to {output_path} ({count_msg:,} bytes)"
                )
            )
        else:
            # Write directly to stdout
            kwargs["stdout"] = sys.stdout
            call_command("dumpdata", *DATA_MODELS, **kwargs)
