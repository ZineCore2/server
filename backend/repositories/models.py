from django.contrib.postgres.fields import ArrayField
from django.db import models

from core.models import BaseVocabulary, TimestampedModel


class RepoKind(BaseVocabulary):
    class Meta(BaseVocabulary.Meta):
        db_table = "repo_kinds"
        verbose_name = "Repository Kind"
        verbose_name_plural = "Repository Kinds"


class Repository(TimestampedModel):
    """RepoCore2: a repository (place that holds zines)."""

    repo_id = models.CharField(
        max_length=64,
        unique=True,
        help_text="Stable external identifier (e.g. 'repo_qzap').",
    )

    name = models.CharField(max_length=255)
    kind = models.CharField(
        max_length=64,
        help_text="Repository type: 'library', 'archive', 'zine-library', 'distro', etc.",
    )

    homepage = models.URLField(blank=True)

    city = models.CharField(max_length=255, blank=True)
    region = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2)

    # External identifiers
    marc_org_code = models.CharField(max_length=16, blank=True)
    isil = models.CharField(max_length=32, blank=True)
    ror_id = models.URLField(blank=True)

    access_policy = models.TextField(blank=True)
    hours = models.TextField(blank=True)
    notes = ArrayField(
        base_field=models.TextField(),
        blank=True,
        default=list,
    )

    class Meta:
        db_table = "repositories"
        verbose_name = "Repository"
        verbose_name_plural = "Repositories"
        indexes = [
            models.Index(fields=["repo_id"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name
