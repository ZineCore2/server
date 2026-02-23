from django.contrib.postgres.fields import ArrayField
from django.db import models

from core.models import BaseVocabulary, TimestampedModel


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


class Agent(TimestampedModel):
    """AgentCore2: agent (person, collective, or organization) associated with zines."""

    agent_id = models.CharField(
        max_length=64,
        unique=True,
        help_text="Stable external identifier (e.g. 'agent_doris').",
    )

    kind = models.CharField(
        max_length=32,
        help_text="Agent type: 'person', 'collective', 'organization', 'other', 'unknown'.",
    )
    display_name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True, null=True)

    aliases = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )
    roles = ArrayField(
        base_field=models.CharField(max_length=64),
        blank=True,
        default=list,
    )

    website = models.URLField(blank=True)
    orcid = models.URLField(blank=True)
    wikidata_id = models.CharField(max_length=32, blank=True)

    public = models.BooleanField(default=True)

    notes = ArrayField(
        base_field=models.TextField(),
        blank=True,
        default=list,
    )

    class Meta:
        db_table = "agents"
        verbose_name = "Agent"
        verbose_name_plural = "Agents"
        indexes = [
            models.Index(fields=["agent_id"]),
            models.Index(fields=["display_name"]),
        ]

    def __str__(self):
        return self.display_name
