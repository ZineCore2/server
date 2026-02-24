from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from core.admin import ExternalIdentifierInline, ExternalUriInline

from .models import Agent, AgentKind, AgentRole


@admin.register(Agent)
class AgentAdmin(ModelAdmin):
    list_display = ["agent_id", "display_name", "kind", "public", "created_at"]
    list_filter = ["kind", "public"]
    search_fields = ["agent_id", "display_name", "aliases"]
    autocomplete_fields = ["kind", "location"]
    readonly_fields = ["agent_id", "created_at", "updated_at"]
    inlines = [ExternalIdentifierInline, ExternalUriInline]
    fieldsets = [
        (None, {"fields": ["agent_id", "display_name", "kind", "location"]}),
        (_("Identity"), {
            "classes": ["tab"],
            "fields": ["legal_name", "aliases"],
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
