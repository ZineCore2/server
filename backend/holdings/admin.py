from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import AccessStatus, DistroStatus, Holding


@admin.register(Holding)
class HoldingAdmin(ModelAdmin):
    list_display = ["repository", "zine", "access_status", "digital_available"]
    list_filter = ["access_status", "distro_status", "digital_available"]
    search_fields = ["call_number", "barcode"]
    autocomplete_fields = ["repository", "zine", "access_status", "distro_status"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["repository", "zine"]}),
        (_("Location"), {
            "classes": ["tab"],
            "fields": ["call_number", "location"],
        }),
        (_("Status"), {
            "classes": ["tab"],
            "fields": ["access_status", "condition", "copy_count", "barcode"],
        }),
        (_("Digital"), {
            "classes": ["tab"],
            "fields": ["digital_available", "digital_url"],
        }),
        (_("Distribution"), {
            "classes": ["tab"],
            "fields": ["distro_status", "notes"],
        }),
        (_("System"), {
            "classes": ["tab"],
            "fields": ["created_at", "updated_at"],
        }),
    ]


@admin.register(AccessStatus)
class AccessStatusAdmin(ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]


@admin.register(DistroStatus)
class DistroStatusAdmin(ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]
