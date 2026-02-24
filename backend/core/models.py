from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint


class TimestampedModel(models.Model):
    """Abstract base for created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class VocabularyManager(models.Manager):
    def get_by_natural_key(self, code):
        return self.get(code=code)


class BaseVocabulary(models.Model):
    """Abstract base for controlled vocabulary models."""

    code = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=255)

    objects = VocabularyManager()

    class Meta:
        abstract = True
        ordering = ["label"]

    def natural_key(self):
        return (self.code,)

    def __str__(self):
        return self.label


# ---------------------------------------------------------------------------
# External Identifier System (controlled vocabulary) + pivot model
# ---------------------------------------------------------------------------


class ExternalIdSystem(BaseVocabulary):
    """Controlled vocabulary of external identifier systems (ISIL, ORCID, ROR, etc.)."""

    class ApplicableTo(models.TextChoices):
        AGENT = "agent", "Agent"
        REPOSITORY = "repository", "Repository"
        BOTH = "both", "Both"

    description = models.TextField(blank=True, default="")
    lookup_uri = models.URLField(
        blank=True,
        default="",
        help_text="URL template/base for looking up a specific identifier value.",
    )
    info_uri = models.URLField(
        blank=True,
        default="",
        help_text="Link to documentation or spec for this identifier system.",
    )
    owner_uri = models.URLField(
        blank=True,
        default="",
        help_text="Link to the responsible authority that manages the standard.",
    )
    applicable_to = models.CharField(
        max_length=16,
        choices=ApplicableTo.choices,
        default=ApplicableTo.BOTH,
    )
    authority_scope = models.ForeignKey(
        "geography.GeoPlace",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Geographic scope of the authority (null = international/global).",
    )

    class Meta(BaseVocabulary.Meta):
        db_table = "external_id_systems"
        verbose_name = "External ID System"
        verbose_name_plural = "External ID Systems"


class ExternalIdentifier(TimestampedModel):
    """An external identifier value attached to an Agent or Repository."""

    system = models.ForeignKey(
        ExternalIdSystem,
        on_delete=models.PROTECT,
        related_name="identifiers",
    )
    agent = models.ForeignKey(
        "agents.Agent",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="external_ids",
    )
    repository = models.ForeignKey(
        "repositories.Repository",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="external_ids",
    )
    value = models.CharField(max_length=255)

    class Meta:
        db_table = "external_identifiers"
        verbose_name = "External Identifier"
        verbose_name_plural = "External Identifiers"
        constraints = [
            CheckConstraint(
                condition=(
                    Q(agent__isnull=False, repository__isnull=True)
                    | Q(agent__isnull=True, repository__isnull=False)
                ),
                name="ext_id_exactly_one_owner",
            ),
            UniqueConstraint(
                fields=["system", "agent"],
                condition=Q(agent__isnull=False),
                name="ext_id_unique_system_agent",
            ),
            UniqueConstraint(
                fields=["system", "repository"],
                condition=Q(repository__isnull=False),
                name="ext_id_unique_system_repository",
            ),
        ]

    def __str__(self):
        owner = self.agent or self.repository
        return f"{self.system.code}:{self.value} ({owner})"


# ---------------------------------------------------------------------------
# External URI Type (controlled vocabulary) + pivot model
# ---------------------------------------------------------------------------


class ExternalUriType(BaseVocabulary):
    """Controlled vocabulary of external URI types (homepage, social media, etc.)."""

    class Category(models.TextChoices):
        WEB = "web", "Web"
        SOCIAL = "social", "Social"
        TECH = "tech", "Tech"

    base_uri = models.URLField(
        blank=True,
        default="",
        help_text="Base URL prefix for the platform, if applicable.",
    )
    category = models.CharField(
        max_length=16,
        choices=Category.choices,
        default=Category.WEB,
    )
    icon = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Material icon name for UI rendering.",
    )

    class Meta(BaseVocabulary.Meta):
        db_table = "external_uri_types"
        verbose_name = "External URI Type"
        verbose_name_plural = "External URI Types"


class ExternalUri(TimestampedModel):
    """An external URI attached to an Agent or Repository."""

    uri_type = models.ForeignKey(
        ExternalUriType,
        on_delete=models.PROTECT,
        related_name="uris",
    )
    agent = models.ForeignKey(
        "agents.Agent",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="external_uris",
    )
    repository = models.ForeignKey(
        "repositories.Repository",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="external_uris",
    )
    uri = models.URLField()

    class Meta:
        db_table = "external_uris"
        verbose_name = "External URI"
        verbose_name_plural = "External URIs"
        constraints = [
            CheckConstraint(
                condition=(
                    Q(agent__isnull=False, repository__isnull=True)
                    | Q(agent__isnull=True, repository__isnull=False)
                ),
                name="ext_uri_exactly_one_owner",
            ),
        ]

    def __str__(self):
        owner = self.agent or self.repository
        return f"{self.uri_type.code}: {self.uri} ({owner})"
