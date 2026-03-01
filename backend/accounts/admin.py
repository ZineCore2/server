from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from .models import Profile, ProfileAgentClaim, ProfileRepositoryClaim, SubmissionStatus, ZineSubmission


class ProfileAgentClaimInline(TabularInline):
    """Inline editor for agent claims on a profile."""

    model = ProfileAgentClaim
    extra = 0
    autocomplete_fields = ["agent"]
    fields = ["agent", "status", "note", "created_at", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]


class ProfileRepositoryClaimInline(TabularInline):
    """Inline editor for repository claims on a profile."""

    model = ProfileRepositoryClaim
    extra = 0
    autocomplete_fields = ["repository"]
    fields = ["repository", "status", "note", "created_at", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ProfileAgentClaim)
class ProfileAgentClaimAdmin(ModelAdmin):
    list_display = ["profile", "agent", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["profile__user__username", "agent__display_name"]
    autocomplete_fields = ["profile", "agent"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["profile", "agent", "status"]}),
        (_("Notes"), {"fields": ["note"]}),
        (
            _("System"),
            {
                "classes": ["tab"],
                "fields": ["created_at", "updated_at"],
            },
        ),
    ]


@admin.register(ProfileRepositoryClaim)
class ProfileRepositoryClaimAdmin(ModelAdmin):
    list_display = ["profile", "repository", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["profile__user__username", "repository__name"]
    autocomplete_fields = ["profile", "repository"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["profile", "repository", "status"]}),
        (_("Notes"), {"fields": ["note"]}),
        (
            _("System"),
            {
                "classes": ["tab"],
                "fields": ["created_at", "updated_at"],
            },
        ),
    ]


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ["user", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "user__email"]
    autocomplete_fields = ["user"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ProfileAgentClaimInline, ProfileRepositoryClaimInline]
    fieldsets = [
        (None, {"fields": ["user", "profile_image"]}),
        (
            _("System"),
            {
                "classes": ["tab"],
                "fields": ["created_at", "updated_at"],
            },
        ),
    ]


@admin.register(ZineSubmission)
class ZineSubmissionAdmin(ModelAdmin):
    list_display = [
        "user",
        "zine",
        "repository",
        "status",
        "send_digital",
        "send_print",
        "submitted_at",
        "responded_at",
    ]
    list_filter = ["status", "send_digital", "send_print", "created_at", "submitted_at", "responded_at"]
    search_fields = ["user__username", "zine__title", "repository__name"]
    autocomplete_fields = ["user", "zine", "repository", "status"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (
            None,
            {"fields": ["user", "zine", "repository", "status"]},
        ),
        (
            _("Submission Details"),
            {
                "classes": ["tab"],
                "fields": ["send_digital", "send_print", "notes"],
            },
        ),
        (
            _("Dates"),
            {
                "classes": ["tab"],
                "fields": ["submitted_at", "responded_at"],
            },
        ),
        (
            _("System"),
            {
                "classes": ["tab"],
                "fields": ["created_at", "updated_at"],
            },
        ),
    ]


@admin.register(SubmissionStatus)
class SubmissionStatusAdmin(ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]
