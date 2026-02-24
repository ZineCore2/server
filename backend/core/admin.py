from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from agents.models import Agent
from catalog.models import Zine
from holdings.models import Holding
from repositories.models import Repository

from .models import ExternalIdentifier, ExternalIdSystem, ExternalUri, ExternalUriType


def dashboard_callback(request, context):
    """Add metric counts to dashboard context."""
    context.update({
        'zine_count': Zine.objects.count(),
        'agent_count': Agent.objects.count(),
        'repository_count': Repository.objects.count(),
        'holding_count': Holding.objects.count(),
    })
    return context


# ---------------------------------------------------------------------------
# Vocabulary admin
# ---------------------------------------------------------------------------


@admin.register(ExternalIdSystem)
class ExternalIdSystemAdmin(ModelAdmin):
    list_display = ["code", "label", "applicable_to", "authority_scope"]
    list_filter = ["applicable_to"]
    search_fields = ["code", "label"]
    autocomplete_fields = ["authority_scope"]


@admin.register(ExternalUriType)
class ExternalUriTypeAdmin(ModelAdmin):
    list_display = ["code", "label", "category", "base_uri"]
    list_filter = ["category"]
    search_fields = ["code", "label"]


# ---------------------------------------------------------------------------
# Inlines for Agent / Repository admin (imported by their respective admin.py)
# ---------------------------------------------------------------------------


class ExternalIdentifierInline(TabularInline):
    model = ExternalIdentifier
    extra = 1
    fields = ["system", "value"]
    autocomplete_fields = ["system"]
    tab = True


class ExternalUriInline(TabularInline):
    model = ExternalUri
    extra = 1
    fields = ["uri_type", "uri"]
    autocomplete_fields = ["uri_type"]
    tab = True
