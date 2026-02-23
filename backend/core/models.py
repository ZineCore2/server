from django.db import models


class TimestampedModel(models.Model):
    """Abstract base for created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseVocabulary(models.Model):
    """Abstract base for controlled vocabulary models."""

    code = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=255)

    class Meta:
        abstract = True
        ordering = ["label"]

    def __str__(self):
        return self.label
