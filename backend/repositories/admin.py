from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from core.admin import ExternalIdentifierInline, ExternalUriInline

from .models import RepoKind, Repository


@admin.register(Repository)
class RepositoryAdmin(ModelAdmin):
    list_display = ["repo_id", "name", "kind", "location", "created_at"]
    list_filter = ["kind"]
    search_fields = ["repo_id", "name", "location__name"]
    autocomplete_fields = ["kind", "location"]
    readonly_fields = ["repo_id", "created_at", "updated_at"]
    inlines = [ExternalIdentifierInline, ExternalUriInline]
    fieldsets = [
        (None, {"fields": ["repo_id", "name", "kind"]}),
        (_("Location"), {
            "classes": ["tab"],
            "fields": ["location", "address"],
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
