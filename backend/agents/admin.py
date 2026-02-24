from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Agent, AgentKind, AgentRole


@admin.register(Agent)
class AgentAdmin(ModelAdmin):
    list_display = ["agent_id", "display_name", "kind", "public", "created_at"]
    list_filter = ["kind", "public"]
    search_fields = ["agent_id", "display_name", "aliases"]
    autocomplete_fields = ["kind"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["agent_id", "display_name", "kind"]}),
        (_("Identity"), {
            "classes": ["tab"],
            "fields": ["legal_name", "aliases"],
        }),
        (_("Links"), {
            "classes": ["tab"],
            "fields": ["website", "orcid", "wikidata_id"],
        }),
        (_("Visibility & Notes"), {
            "classes": ["tab"],
            "fields": ["public", "notes"],
        }),
        (_("System"), {
            "classes": ["tab"],
            "fields": ["created_at", "updated_at"],
        }),
    ]


@admin.register(AgentKind)
class AgentKindAdmin(ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]


@admin.register(AgentRole)
class AgentRoleAdmin(ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]
