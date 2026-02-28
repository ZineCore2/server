from pathlib import Path

from django.core import serializers
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Export user-created data to two files: "
        "fixtures.json (repositories and their external IDs/URIs) and "
        "custom.json (agents, zines, holdings, submissions, profiles, and their external IDs/URIs)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default="data",
            help="Output directory for exported files (default: data).",
        )
        parser.add_argument(
            "--indent",
            type=int,
            default=2,
            help="JSON indentation level (default: 2).",
        )

    def handle(self, *args, **options):
        from accounts.models import Profile, ZineSubmission
        from agents.models import Agent
        from catalog.models import Zine, ZineContributor, ZineCreator, ZinePublisher
        from core.models import ExternalIdentifier, ExternalUri
        from holdings.models import Holding
        from repositories.models import Repository

        output_dir = Path(options["output_dir"])
        indent = options["indent"]

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export fixtures.json (repositories and their external IDs/URIs)
        fixtures_path = output_dir / "fixtures.json"
        fixture_objects = []

        # Add all repositories
        fixture_objects.extend(Repository.objects.all())

        # Add repository-related external identifiers and URIs
        fixture_objects.extend(
            ExternalIdentifier.objects.filter(repository__isnull=False)
        )
        fixture_objects.extend(
            ExternalUri.objects.filter(repository__isnull=False)
        )

        self._export_objects(fixture_objects, fixtures_path, indent, "repositories")

        # Export custom.json (agents, zines, holdings, and their external IDs/URIs)
        custom_path = output_dir / "custom.json"
        custom_objects = []

        # Add all agents (must come before zines due to FK references)
        custom_objects.extend(Agent.objects.all())

        # Add agent-related external identifiers and URIs
        custom_objects.extend(
            ExternalIdentifier.objects.filter(agent__isnull=False)
        )
        custom_objects.extend(
            ExternalUri.objects.filter(agent__isnull=False)
        )

        # Add all zines and their through models
        custom_objects.extend(Zine.objects.all())
        custom_objects.extend(ZineCreator.objects.all())
        custom_objects.extend(ZineContributor.objects.all())
        custom_objects.extend(ZinePublisher.objects.all())

        # Add all holdings
        custom_objects.extend(Holding.objects.all())

        # Add all zine submissions
        custom_objects.extend(ZineSubmission.objects.all())

        # Add all user profiles
        custom_objects.extend(Profile.objects.all())

        self._export_objects(custom_objects, custom_path, indent, "agents, zines, holdings, submissions, and profiles")

    def _export_objects(self, objects, output_path, indent, description):
        """Serialize objects to JSON fixture file."""
        json_data = serializers.serialize(
            "json",
            objects,
            indent=indent,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=False,
        )

        output_path.write_text(json_data)
        file_size = output_path.stat().st_size

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {description} to {output_path} ({file_size:,} bytes)"
            )
        )
