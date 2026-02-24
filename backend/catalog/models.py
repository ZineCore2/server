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


class Language(BaseVocabulary):
    class Meta(BaseVocabulary.Meta):
        db_table = "languages"
        verbose_name = "Language"
        verbose_name_plural = "Languages"


class Zine(TimestampedModel):
    """ZineCore2: single zine issue description."""

    zine_id = models.CharField(
        max_length=64,
        unique=True,
        help_text="Stable external identifier (e.g. 'zine_mutate_3_1st').",
    )

    title = models.CharField(max_length=512)

    # Series / issue / edition
    series_title = models.CharField(max_length=512, blank=True, default="")
    issue_designation = models.CharField(max_length=255, blank=True, null=True)
    edition_statement = models.CharField(max_length=255, blank=True, default="")
    alternative_title = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )

    # Creators / contributors
    creators = models.ManyToManyField(
        "agents.Agent",
        through="ZineCreator",
        related_name="zines_created",
        blank=True,
    )
    contributors = models.ManyToManyField(
        "agents.Agent",
        through="ZineContributor",
        related_name="zines_contributed",
        blank=True,
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
    publishers = models.ManyToManyField(
        "agents.Agent",
        through="ZinePublisher",
        related_name="zines_published",
        blank=True,
    )
    publish_date = models.DateField(null=True, blank=True)

    # Physical description
    physical_dimensions = models.CharField(max_length=255, blank=True)
    number_of_pages = models.CharField(max_length=64, blank=True)
    format = models.CharField(max_length=255, blank=True, default="")
    binding_features = models.CharField(max_length=255, blank=True, default="")

    # Language & coverage
    languages = models.ManyToManyField(Language, related_name="zines", blank=True)
    place_of_publication = models.CharField(max_length=255, blank=True, default="")
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
    rights_statement = models.ForeignKey(
        RightsStatement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="zines",
    )
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


class ZineCreator(models.Model):
    """Through model for Zine creators with ordering."""

    zine = models.ForeignKey(Zine, on_delete=models.CASCADE)
    agent = models.ForeignKey("agents.Agent", on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "zine_creators"
        verbose_name = "Zine Creator"
        verbose_name_plural = "Zine Creators"
        unique_together = [["zine", "agent", "order"]]
        ordering = ["order"]

    def __str__(self):
        return f"{self.agent.display_name} (creator of {self.zine.title})"


class ZineContributor(models.Model):
    """Through model for Zine contributors with role and ordering."""

    zine = models.ForeignKey(Zine, on_delete=models.CASCADE)
    agent = models.ForeignKey("agents.Agent", on_delete=models.CASCADE)
    role = models.ForeignKey("agents.AgentRole", on_delete=models.PROTECT)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "zine_contributors"
        verbose_name = "Zine Contributor"
        verbose_name_plural = "Zine Contributors"
        unique_together = [["zine", "agent", "role"]]
        ordering = ["order"]

    def __str__(self):
        return f"{self.agent.display_name} ({self.role.label} for {self.zine.title})"


class ZinePublisher(models.Model):
    """Through model for Zine publishers with ordering."""

    zine = models.ForeignKey(Zine, on_delete=models.CASCADE)
    agent = models.ForeignKey("agents.Agent", on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "zine_publishers"
        verbose_name = "Zine Publisher"
        verbose_name_plural = "Zine Publishers"
        unique_together = [["zine", "agent", "order"]]
        ordering = ["order"]

    def __str__(self):
        return f"{self.agent.display_name} (publisher of {self.zine.title})"
