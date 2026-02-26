"""Custom admin views for data management."""

import json
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from .forms import ImportJSONForm


@method_decorator(staff_member_required, name="dispatch")
class ImportJSONView(View):
    """Admin view for importing JSON data."""

    template_name = "admin/import_json.html"

    def _get_importers(self):
        """Lazy-load importers to avoid circular import issues."""
        from .importers import AgentImporter, RepositoryImporter, ZineImporter

        return {
            "zinecore2": ZineImporter,
            "agentcore2": AgentImporter,
            "repocore2": RepositoryImporter,
            # "holdingcore2": HoldingImporter,  # TODO: Implement
        }

    def get(self, request):
        """Display the import form."""
        form = ImportJSONForm()
        context = {
            **admin.site.each_context(request),
            "form": form,
            "title": "Import JSON Data",
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Process the JSON import."""
        form = ImportJSONForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "title": "Import JSON Data"})

        # Get form data
        json_data = form.cleaned_data["json_data"]
        schema_type = form.cleaned_data["schema_type"]
        atomic = form.cleaned_data["atomic_import"]
        validate_only = form.cleaned_data["validate_only"]

        # Parse JSON
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            messages.error(request, f"Invalid JSON: {str(e)}")
            return render(request, self.template_name, {"form": form, "title": "Import JSON Data"})

        # Convert single object to list
        if isinstance(data, dict):
            data_list = [data]
        elif isinstance(data, list):
            data_list = data
        else:
            messages.error(request, "JSON must be an object or array of objects")
            return render(request, self.template_name, {"form": form, "title": "Import JSON Data"})

        # Auto-detect schema if needed
        if schema_type == "auto":
            schema_type = self._detect_schema(data_list[0])
            if not schema_type:
                messages.error(
                    request,
                    "Could not auto-detect schema type. Please select manually.",
                )
                return render(request, self.template_name, {"form": form, "title": "Import JSON Data"})

        # Get importer
        importers = self._get_importers()
        importer_class = importers.get(schema_type)
        if not importer_class:
            messages.error(request, f"Unsupported schema type: {schema_type}")
            return render(request, self.template_name, {"form": form, "title": "Import JSON Data"})

        # Run import
        importer = importer_class()
        try:
            result = importer.import_batch(
                data_list, atomic=atomic, validate_only=validate_only
            )
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")
            return render(request, self.template_name, {"form": form, "title": "Import JSON Data"})

        # Display results
        context = {
            **admin.site.each_context(request),
            "form": ImportJSONForm(),  # Fresh form for next import
            "title": "Import JSON Data",
            "result": result,
            "schema_type": schema_type,
            "validate_only": validate_only,
        }

        # Add success/error messages
        if validate_only:
            if result.is_successful:
                messages.success(
                    request,
                    f"✓ Validation successful: {result.successful} records valid",
                )
            else:
                messages.warning(
                    request,
                    f"Validation completed: {result.successful} valid, {result.failed} errors",
                )
        else:
            if result.is_successful:
                created = len(result.created_ids)
                updated = len(result.updated_ids)
                msg = f"✓ Import successful: {created} created, {updated} updated"
                messages.success(request, msg)
            else:
                if result.successful > 0:
                    created = len(result.created_ids)
                    updated = len(result.updated_ids)
                    msg = f"Partial success: {created} created, {updated} updated, {result.failed} failed"
                    messages.warning(request, msg)
                else:
                    messages.error(
                        request, f"✗ Import failed: {result.failed} errors"
                    )

        return render(request, self.template_name, context)

    def _detect_schema(self, data: dict) -> str:
        """Auto-detect schema type from JSON data."""
        if not isinstance(data, dict):
            return None

        # Check for distinctive fields
        if "zine_id" in data or (
            "title" in data and ("creator" in data or "subject" in data)
        ):
            return "zinecore2"
        elif "agent_id" in data or "display_name" in data:
            return "agentcore2"
        elif "repo_id" in data or ("name" in data and "kind" in data and "country" in data):
            return "repocore2"
        elif "repository_id" in data and "zine_id" in data:
            return "holdingcore2"

        return None
