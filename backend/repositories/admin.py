from django.contrib import admin

from .models import RepoKind, Repository


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ["repo_id", "name", "kind", "city", "country", "created_at"]
    list_filter = ["kind", "country"]
    search_fields = ["repo_id", "name", "city"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(RepoKind)
class RepoKindAdmin(admin.ModelAdmin):
    list_display = ["code", "label"]
    search_fields = ["code", "label"]
