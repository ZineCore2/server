from django.contrib.postgres.fields import ArrayField
from django.db import models
from django_extensions.db.fields import AutoSlugField

from core.models import BaseVocabulary, TimestampedModel
from geography.models import GeoPlace


class AgentKind(BaseVocabulary):
    class Meta(BaseVocabulary.Meta):
        db_table = "agent_kinds"
        verbose_name = "Agent Kind"
        verbose_name_plural = "Agent Kinds"


class AgentRole(BaseVocabulary):
    class Meta(BaseVocabulary.Meta):
        db_table = "agent_roles"
        verbose_name = "Agent Role"
        verbose_name_plural = "Agent Roles"


class AgentManager(models.Manager):
    def get_by_natural_key(self, agent_id):
        return self.get(agent_id=agent_id)


class Agent(TimestampedModel):
    """AgentCore2: agent (person, collective, or organization) associated with zines."""

    agent_id = AutoSlugField(
        max_length=64,
        unique=True,
        populate_from="slug_source",
        help_text="Auto-generated slug (e.g. 'a-doris').",
    )

    kind = models.ForeignKey(
        AgentKind,
        on_delete=models.PROTECT,
        related_name="agents",
        help_text="Agent type: 'person', 'collective', 'organization', 'other', 'unknown'.",
    )
    display_name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True, null=True)

    aliases = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )

    location = models.ForeignKey(
        GeoPlace,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agents",
        help_text="Geographic location from GeoNames hierarchy.",
    )

    public = models.BooleanField(default=True)

    notes = ArrayField(
        base_field=models.TextField(),
        blank=True,
        default=list,
    )

    objects = AgentManager()

    class Meta:
        db_table = "agents"
        verbose_name = "Agent"
        verbose_name_plural = "Agents"
        indexes = [
            models.Index(fields=["agent_id"]),
            models.Index(fields=["display_name"]),
        ]

    def natural_key(self):
        return (self.agent_id,)

    def slug_source(self):
        return f"a {self.display_name}"

    def __str__(self):
        return self.display_name
