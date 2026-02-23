from django.contrib import admin

from .models import Genre, RightsStatement, Subject, Zine


@admin.register(Zine)
class ZineAdmin(admin.ModelAdmin):
    list_display = ["zine_id", "title", "created_at"]
    search_fields = ["zine_id", "title"]
    readonly_fields = ["created_at", "updated_at"]
    filter_horizontal = ["subjects", "genres"]
    fieldsets = [
        ("Identification", {"fields": [
            "zine_id", "title", "series_title", "issue_designation",
            "edition_statement", "alternative_title",
        ]}),
        ("Creators", {"fields": ["creator", "contributor"]}),
        ("Classification", {"fields": ["subject", "subjects", "genre", "genres"]}),
        ("Description", {"fields": ["abstract", "table_of_contents", "public_notes"]}),
        ("Publication", {"fields": ["publisher", "date", "place_of_publication"]}),
        ("Physical", {"fields": [
            "physical_dimensions", "number_of_pages", "format", "binding_features",
        ]}),
        ("Language & Coverage", {"fields": ["language", "coverage"]}),
        ("Provenance & Relations", {"fields": [
            "source", "relation", "rights", "identifier",
        ]}),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]


@admin.register(RightsStatement)
class RightsStatementAdmin(admin.ModelAdmin):
    list_display = ["code", "label", "uri"]
    search_fields = ["code", "label"]
