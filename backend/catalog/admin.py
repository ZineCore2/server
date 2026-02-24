from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Genre,
    Language,
    RightsStatement,
    Subject,
    Zine,
    ZineContributor,
    ZineCreator,
    ZinePublisher,
)


class ZineCreatorInline(TabularInline):
    model = ZineCreator
    extra = 1
    fields = ["agent", "order"]
    autocomplete_fields = ["agent"]


class ZineContributorInline(TabularInline):
    model = ZineContributor
    extra = 1
    fields = ["agent", "role", "order"]
    autocomplete_fields = ["agent", "role"]


class ZinePublisherInline(TabularInline):
    model = ZinePublisher
    extra = 1
    fields = ["agent", "order"]
    autocomplete_fields = ["agent"]


@admin.register(Zine)
class ZineAdmin(ModelAdmin):
    list_display = ["zine_id", "title", "created_at"]
    search_fields = ["zine_id", "title"]
    autocomplete_fields = ["rights_statement"]
    filter_horizontal = ["subjects", "genres", "languages"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ZineCreatorInline, ZineContributorInline, ZinePublisherInline]
    fieldsets = [
        (None, {"fields": ["zine_id", "title"]}),
        (_("Series & Edition"), {
            "classes": ["tab"],
            "fields": [
                "series_title", "issue_designation",
                "edition_statement", "alternative_title",
            ],
        }),
        (_("Classification"), {
            "classes": ["tab"],
            "fields": ["subjects", "genres"],
        }),
        (_("Description"), {
            "classes": ["tab"],
            "fields": ["abstract", "table_of_contents", "public_notes"],
        }),
        (_("Publication"), {
            "classes": ["tab"],
            "fields": ["publish_date", "place_of_publication"],
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
            "fields": ["languages", "coverage"],
        }),
        (_("Rights & Relations"), {
            "classes": ["tab"],
            "fields": ["source", "relation", "rights_statement", "identifier"],
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


@admin.register(Language)
class LanguageAdmin(ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]
