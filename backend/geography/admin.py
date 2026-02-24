from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import GeoPlace


@admin.register(GeoPlace)
class GeoPlaceAdmin(ModelAdmin):
    list_display = ["geoname_id", "name", "feature_code", "country_code", "parent", "population"]
    list_filter = ["feature_code", "continent_code"]
    search_fields = ["name", "ascii_name", "geoname_id"]
    readonly_fields = [
        "geoname_id", "name", "ascii_name", "feature_class", "feature_code",
        "country_code", "admin1_code", "continent_code",
        "latitude", "longitude", "population", "parent",
    ]
    list_per_page = 50
