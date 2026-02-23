from django.contrib import admin

from .models import AccessStatus, DistroStatus, Holding


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ["holding_id", "repository", "zine", "access_status", "digital_available"]
    list_filter = ["access_status", "distro_status", "digital_available"]
    search_fields = ["holding_id", "call_number", "barcode"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["repository", "zine"]


@admin.register(AccessStatus)
class AccessStatusAdmin(admin.ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]


@admin.register(DistroStatus)
class DistroStatusAdmin(admin.ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]
