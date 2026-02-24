from django.contrib.postgres.fields import ArrayField
from django.db import models
from django_extensions.db.fields import AutoSlugField

from core.models import BaseVocabulary, TimestampedModel
from geography.models import GeoPlace


class RepoKind(BaseVocabulary):
    class Meta(BaseVocabulary.Meta):
        db_table = "repo_kinds"
        verbose_name = "Repository Kind"
        verbose_name_plural = "Repository Kinds"


class RepositoryManager(models.Manager):
    def get_by_natural_key(self, repo_id):
        return self.get(repo_id=repo_id)


class Repository(TimestampedModel):
    """RepoCore2: a repository (place that holds zines)."""

    repo_id = AutoSlugField(
        max_length=64,
        unique=True,
        populate_from="slug_source",
        help_text="Auto-generated slug (e.g. 'r-qzap').",
    )

    name = models.CharField(max_length=255)
    kind = models.ForeignKey(
        RepoKind,
        on_delete=models.PROTECT,
        related_name="repositories",
        help_text="Repository type: 'library', 'archive', 'zine-library', 'distro', etc.",
    )

    address = models.TextField(blank=True)
    location = models.ForeignKey(
        GeoPlace,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="repositories",
        help_text="Geographic location from GeoNames hierarchy.",
    )

    access_policy = models.TextField(blank=True)
    hours = models.TextField(blank=True)
    notes = ArrayField(
        base_field=models.TextField(),
        blank=True,
        default=list,
    )

    objects = RepositoryManager()

    class Meta:
        db_table = "repositories"
        verbose_name = "Repository"
        verbose_name_plural = "Repositories"
        indexes = [
            models.Index(fields=["repo_id"]),
            models.Index(fields=["name"]),
        ]

    def natural_key(self):
        return (self.repo_id,)

    def slug_source(self):
        return f"r {self.name}"

    def __str__(self):
        return self.name
