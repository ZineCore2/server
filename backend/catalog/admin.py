from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Genre, RightsStatement, Subject, Zine


@admin.register(Zine)
class ZineAdmin(ModelAdmin):
    list_display = ["zine_id", "title", "created_at"]
    search_fields = ["zine_id", "title"]
    readonly_fields = ["created_at", "updated_at"]
    filter_horizontal = ["subjects", "genres"]
    fieldsets = [
        (None, {"fields": ["zine_id", "title"]}),
        (_("Series & Edition"), {
            "classes": ["tab"],
            "fields": [
                "series_title", "issue_designation",
                "edition_statement", "alternative_title",
            ],
        }),
        (_("Creators"), {
            "classes": ["tab"],
            "fields": ["creator", "contributor"],
        }),
        (_("Classification"), {
            "classes": ["tab"],
            "fields": ["subject", "subjects", "genre", "genres"],
        }),
        (_("Description"), {
            "classes": ["tab"],
            "fields": ["abstract", "table_of_contents", "public_notes"],
        }),
        (_("Publication"), {
            "classes": ["tab"],
            "fields": ["publisher", "date", "place_of_publication"],
        }),
        (_("Physical"), {
            "classes": ["tab"],
            "fields": [
                "physical_dimensions", "number_of_pages",
                "format", "binding_features",
            ],
        }),
        (_("Language & Coverage"), {
            "classes": ["tab"],
            "fields": ["language", "coverage"],
        }),
        (_("Rights & Relations"), {
            "classes": ["tab"],
            "fields": ["source", "relation", "rights", "identifier"],
        }),
        (_("System"), {
            "classes": ["tab"],
            "fields": ["created_at", "updated_at"],
        }),
    ]


@admin.register(Subject)
class SubjectAdmin(ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]


@admin.register(Genre)
class GenreAdmin(ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]


@admin.register(RightsStatement)
class RightsStatementAdmin(ModelAdmin):
    list_display = ["code", "label", "uri"]
    search_fields = ["code", "label"]
