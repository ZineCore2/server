from django.contrib import admin

from .models import Agent, AgentKind, AgentRole


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ["agent_id", "display_name", "kind", "public", "created_at"]
    list_filter = ["kind", "public"]
    search_fields = ["agent_id", "display_name", "aliases"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(AgentKind)
class AgentKindAdmin(admin.ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]


@admin.register(AgentRole)
class AgentRoleAdmin(admin.ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]
