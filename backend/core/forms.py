"""Forms for core admin functionality."""

from django import forms


class ImportJSONForm(forms.Form):
    """Form for importing JSON data via paste."""

    SCHEMA_CHOICES = [
        ("auto", "Auto-detect"),
        ("zinecore2", "ZineCore2 (Zines)"),
        ("agentcore2", "AgentCore2 (Agents)"),
        ("repocore2", "RepoCore2 (Repositories)"),
        ("holdingcore2", "HoldingCore2 (Holdings)"),
    ]

    json_data = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 20,
                "placeholder": "Paste JSON here (single object or array of objects)...",
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100",
            }
        ),
        label="JSON Data",
        help_text="Paste a single JSON object or an array of objects conforming to any ZineCore2 schema.",
    )

    schema_type = forms.ChoiceField(
        choices=SCHEMA_CHOICES,
        initial="auto",
        label="Schema Type",
        help_text="Select the schema type or let the system auto-detect it.",
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100",
            }
        ),
    )

    atomic_import = forms.BooleanField(
        initial=True,
        required=False,
        label="All-or-Nothing Import",
        help_text="If checked, the entire import will roll back if any record fails. If unchecked, valid records will be imported even if some fail.",
        widget=forms.CheckboxInput(
            attrs={
                "class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800",
            }
        ),
    )

    validate_only = forms.BooleanField(
        initial=False,
        required=False,
        label="Validate Only (Don't Import)",
        help_text="If checked, only validate the JSON without importing to the database.",
        widget=forms.CheckboxInput(
            attrs={
                "class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800",
            }
        ),
    )
