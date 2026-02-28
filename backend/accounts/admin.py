from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Profile, SubmissionStatus, ZineSubmission


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ["user", "agent", "repository"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "user__email"]
    autocomplete_fields = ["user", "agent", "repository"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["user", "profile_image"]}),
        (
            _("Associations"),
            {
                "classes": ["tab"],
                "fields": ["agent", "repository"],
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
