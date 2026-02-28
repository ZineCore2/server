from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RelatedDropdownFilter

from core.admin import ExternalIdentifierInline, ExternalUriInline

from .models import RepoKind, Repository


@admin.register(Repository)
class RepositoryAdmin(ModelAdmin):
    list_display = ["name", "kind", "is_active", "submission_allowed", "full_location_display",]
    list_filter = [
        ("kind", RelatedDropdownFilter),
        "is_active",
        "submission_allowed",
    ]
    list_filter_submit = True
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
        (_("Status & Submission"), {
            "classes": ["tab"],
            "fields": [
                "is_active",
                ("submission_allowed", "submission_notes"),
            ],
        }),
        (_("System"), {
            "classes": ["tab"],
            "fields": ["created_at", "updated_at"],
        }),
    ]

    @admin.display(description="Location", ordering="location__name")
    def full_location_display(self, obj):
        """Display full geographic hierarchy for location."""
        if obj.location:
            return obj.location.full_display_name
        return "-"

    @admin.display(description="Level", ordering="location__feature_code")
    def location_level(self, obj):
        """Display geographic level of location."""
        if obj.location:
            return obj.location.level
        return "-"


@admin.register(RepoKind)
class RepoKindAdmin(ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]
