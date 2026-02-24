"""Data migration: copy legacy hardcoded external ID and URL fields into
the new ExternalIdentifier / ExternalUri pivot tables.

Agent fields migrated:
  - website  → ExternalUri (type=homepage)
  - orcid    → ExternalIdentifier (system=orcid)
  - wikidata_id → ExternalIdentifier (system=wikidata)

Repository fields migrated:
  - homepage      → ExternalUri (type=homepage)
  - marc_org_code → ExternalIdentifier (system=marc_org)
  - isil          → ExternalIdentifier (system=isil)
  - ror_id        → ExternalIdentifier (system=ror)
"""

from django.db import migrations


def forwards(apps, schema_editor):
    ExternalIdSystem = apps.get_model("core", "ExternalIdSystem")
    ExternalIdentifier = apps.get_model("core", "ExternalIdentifier")
    ExternalUriType = apps.get_model("core", "ExternalUriType")
    ExternalUri = apps.get_model("core", "ExternalUri")
    Agent = apps.get_model("agents", "Agent")
    Repository = apps.get_model("repositories", "Repository")

    # Pre-fetch vocabulary records
    id_systems = {s.code: s for s in ExternalIdSystem.objects.all()}
    uri_types = {t.code: t for t in ExternalUriType.objects.all()}

    # --- Agents ---
    for agent in Agent.objects.all():
        if agent.website:
            ExternalUri.objects.get_or_create(
                uri_type=uri_types["homepage"],
                agent=agent,
                defaults={"uri": agent.website},
            )
        if agent.orcid:
            ExternalIdentifier.objects.get_or_create(
                system=id_systems["orcid"],
                agent=agent,
                defaults={"value": agent.orcid},
            )
        if agent.wikidata_id:
            ExternalIdentifier.objects.get_or_create(
                system=id_systems["wikidata"],
                agent=agent,
                defaults={"value": agent.wikidata_id},
            )

    # --- Repositories ---
    for repo in Repository.objects.all():
        if repo.homepage:
            ExternalUri.objects.get_or_create(
                uri_type=uri_types["homepage"],
                repository=repo,
                defaults={"uri": repo.homepage},
            )
        if repo.marc_org_code:
            ExternalIdentifier.objects.get_or_create(
                system=id_systems["marc_org"],
                repository=repo,
                defaults={"value": repo.marc_org_code},
            )
        if repo.isil:
            ExternalIdentifier.objects.get_or_create(
                system=id_systems["isil"],
                repository=repo,
                defaults={"value": repo.isil},
            )
        if repo.ror_id:
            ExternalIdentifier.objects.get_or_create(
                system=id_systems["ror"],
                repository=repo,
                defaults={"value": repo.ror_id},
            )


def backwards(apps, schema_editor):
    """Reverse: copy pivot rows back to legacy fields."""
    ExternalIdentifier = apps.get_model("core", "ExternalIdentifier")
    ExternalUri = apps.get_model("core", "ExternalUri")

    # Agents
    for ext_uri in ExternalUri.objects.filter(
        agent__isnull=False, uri_type__code="homepage"
    ).select_related("agent"):
        ext_uri.agent.website = ext_uri.uri
        ext_uri.agent.save(update_fields=["website"])

    for ext_id in ExternalIdentifier.objects.filter(
        agent__isnull=False
    ).select_related("agent", "system"):
        if ext_id.system.code == "orcid":
            ext_id.agent.orcid = ext_id.value
            ext_id.agent.save(update_fields=["orcid"])
        elif ext_id.system.code == "wikidata":
            ext_id.agent.wikidata_id = ext_id.value
            ext_id.agent.save(update_fields=["wikidata_id"])

    # Repositories
    for ext_uri in ExternalUri.objects.filter(
        repository__isnull=False, uri_type__code="homepage"
    ).select_related("repository"):
        ext_uri.repository.homepage = ext_uri.uri
        ext_uri.repository.save(update_fields=["homepage"])

    field_map = {
        "marc_org": "marc_org_code",
        "isil": "isil",
        "ror": "ror_id",
    }
    for ext_id in ExternalIdentifier.objects.filter(
        repository__isnull=False
    ).select_related("repository", "system"):
        field_name = field_map.get(ext_id.system.code)
        if field_name:
            setattr(ext_id.repository, field_name, ext_id.value)
            ext_id.repository.save(update_fields=[field_name])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_external_models"),
        ("agents", "0004_agent_location"),
        ("repositories", "0007_external_models"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
