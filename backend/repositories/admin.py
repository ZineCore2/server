from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Country, RepoKind, Repository


@admin.register(Repository)
class RepositoryAdmin(ModelAdmin):
    list_display = ["repo_id", "name", "kind", "city", "country", "created_at"]
    list_filter = ["kind", "country"]
    search_fields = ["repo_id", "name", "city"]
    autocomplete_fields = ["kind", "country"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["repo_id", "name", "kind"]}),
        (_("Location"), {
            "classes": ["tab"],
            "fields": ["homepage", "city", "region", "country"],
        }),
        (_("Identifiers"), {
            "classes": ["tab"],
            "fields": ["marc_org_code", "isil", "ror_id"],
        }),
        (_("Operations"), {
            "classes": ["tab"],
            "fields": ["access_policy", "hours", "notes"],
        }),
        (_("System"), {
            "classes": ["tab"],
            "fields": ["created_at", "updated_at"],
        }),
    ]


@admin.register(RepoKind)
class RepoKindAdmin(ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]


@admin.register(Country)
class CountryAdmin(ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]
