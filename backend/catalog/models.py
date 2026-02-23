from django.contrib.postgres.fields import ArrayField
from django.db import models

from core.models import BaseVocabulary, TimestampedModel


class Subject(BaseVocabulary):
    class Meta(BaseVocabulary.Meta):
        db_table = "subjects"
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"


class Genre(BaseVocabulary):
    class Meta(BaseVocabulary.Meta):
        db_table = "genres"
        verbose_name = "Genre"
        verbose_name_plural = "Genres"


class RightsStatement(BaseVocabulary):
    uri = models.URLField(blank=True, default="")
    description = models.TextField(blank=True, default="")

    class Meta(BaseVocabulary.Meta):
        db_table = "rights_statements"
        verbose_name = "Rights Statement"
        verbose_name_plural = "Rights Statements"


class Zine(TimestampedModel):
    """ZineCore2: single zine issue description."""

    zine_id = models.CharField(
        max_length=64,
        unique=True,
        help_text="Stable external identifier (e.g. 'zine_mutate_3_1st').",
    )

    title = models.CharField(max_length=512)

    # Series / issue / edition
    series_title = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )
    issue_designation = models.CharField(max_length=255, blank=True, null=True)
    edition_statement = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )
    alternative_title = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )

    # Creators / contributors
    creator = ArrayField(base_field=models.CharField(max_length=255))
    contributor = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )

    # Subjects / genres: controlled vocabulary links
    subjects = models.ManyToManyField(Subject, related_name="zines")
    genres = models.ManyToManyField(Genre, related_name="zines")

    # Descriptive text
    abstract = models.TextField(blank=True)
    table_of_contents = models.TextField(blank=True)
    public_notes = ArrayField(
        base_field=models.TextField(),
        blank=True,
        default=list,
    )

    # Publication
    publisher = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )
    date = ArrayField(base_field=models.CharField(max_length=64))

    # Physical description
    physical_dimensions = models.CharField(max_length=255, blank=True)
    number_of_pages = models.CharField(max_length=64, blank=True)
    format = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )
    binding_features = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )

    # Language & coverage
    language = ArrayField(base_field=models.CharField(max_length=16))
    place_of_publication = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )
    coverage = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )

    # Provenance / relations / rights
    source = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )
    relation = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )
    rights = ArrayField(base_field=models.CharField(max_length=255))
    identifier = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )

    class Meta:
        db_table = "zines"
        verbose_name = "Zine"
        verbose_name_plural = "Zines"
        indexes = [
            models.Index(fields=["zine_id"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return self.title
