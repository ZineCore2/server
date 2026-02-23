from django.contrib.postgres.fields import ArrayField
from django.db import models

from catalog.models import Zine
from core.models import BaseVocabulary, TimestampedModel
from repositories.models import Repository


class AccessStatus(BaseVocabulary):
    class Meta(BaseVocabulary.Meta):
        db_table = "holding_access_statuses"
        verbose_name = "Access Status"
        verbose_name_plural = "Access Statuses"


class DistroStatus(BaseVocabulary):
    class Meta(BaseVocabulary.Meta):
        db_table = "holding_distro_statuses"
        verbose_name = "Distribution Status"
        verbose_name_plural = "Distribution Statuses"


class Holding(TimestampedModel):
    """HoldingCore2: a specific holding (copy/item) of a zine at a repository."""

    holding_id = models.CharField(
        max_length=64,
        unique=True,
        help_text="Stable external identifier (e.g. 'holding_qzap_heavy_mayo_1').",
    )

    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="holdings",
    )
    zine = models.ForeignKey(
        Zine,
        on_delete=models.CASCADE,
        related_name="holdings",
    )

    call_number = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)

    access_status = models.CharField(max_length=64, blank=True)
    condition = models.CharField(max_length=64, blank=True)
    copy_count = models.PositiveIntegerField(blank=True, null=True)
    barcode = models.CharField(max_length=64, blank=True)

    digital_available = models.BooleanField(default=False)
    digital_url = models.URLField(blank=True)

    distro_status = models.CharField(max_length=64, blank=True)

    notes = ArrayField(
        base_field=models.TextField(),
        blank=True,
        default=list,
    )

    class Meta:
        db_table = "holdings"
        verbose_name = "Holding"
        verbose_name_plural = "Holdings"
        indexes = [
            models.Index(fields=["holding_id"]),
            models.Index(fields=["repository", "zine"]),
        ]

    def __str__(self):
        return f"{self.holding_id} ({self.repository} \u2013 {self.zine})"
