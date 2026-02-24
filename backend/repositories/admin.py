from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import RepoKind, Repository


@admin.register(Repository)
class RepositoryAdmin(ModelAdmin):
    list_display = ["repo_id", "name", "kind", "location", "created_at"]
    list_filter = ["kind"]
    search_fields = ["repo_id", "name", "location__name"]
    autocomplete_fields = ["kind", "location"]
    readonly_fields = ["repo_id", "created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["repo_id", "name", "kind"]}),
        (_("Location"), {
            "classes": ["tab"],
            "fields": [
                "address", 
                ("location","homepage"),
            ],
        }),
        (_("Identifiers"), {
            "classes": ["tab"],
            "fields": [("marc_org_code", "isil", "ror_id"),],
        }),
        (_("Operations"), {
            "classes": ["tab"],
            "fields": [
                ("access_policy", "hours", "notes")
            ],
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
