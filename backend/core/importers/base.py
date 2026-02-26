"""Base importer class for JSON schema imports."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Type

from django.conf import settings
from django.db import models, transaction
from rest_framework import serializers

try:
    import jsonschema
except ImportError:
    jsonschema = None


@dataclass
class ImportError:
    """Represents an error that occurred during import."""

    record_index: int
    record_id: Optional[str] = None
    error_type: str = "unknown"  # "schema", "validation", "database"
    field: Optional[str] = None
    message: str = ""

    def __str__(self):
        id_str = f" (id: {self.record_id})" if self.record_id else ""
        field_str = f" [{self.field}]" if self.field else ""
        return f"Record #{self.record_index}{id_str}{field_str}: {self.message}"


@dataclass
class ImportResult:
    """Result of importing JSON data."""

    total_records: int = 0
    successful: int = 0
    failed: int = 0
    errors: list[ImportError] = field(default_factory=list)
    created_ids: list[str] = field(default_factory=list)
    updated_ids: list[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def is_successful(self) -> bool:
        return self.failed == 0


class BaseImporter(ABC):
    """Abstract base class for schema-specific importers."""

    # Subclasses must define these
    schema_name: str = ""
    model: Type[models.Model] = None
    write_serializer: Type[serializers.Serializer] = None
    id_field: str = ""  # Natural key field name (e.g., "zine_id", "agent_id")

    def __init__(self):
        self.result = ImportResult()

    @property
    def schema_path(self) -> Path:
        """Path to the JSON schema file."""
        return (
            Path(settings.BASE_DIR).parent
            / "spec"
            / "schemas"
            / f"{self.schema_name}.schema.json"
        )

    def load_schema(self) -> dict:
        """Load the JSON schema from file."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        with open(self.schema_path) as f:
            return json.load(f)

    def validate_schema(self, data: dict) -> tuple[bool, Optional[str]]:
        """
        Validate data against JSON Schema.

        Returns:
            (is_valid, error_message)
        """
        if jsonschema is None:
            return True, None  # Skip validation if jsonschema not installed

        try:
            schema = self.load_schema()
            jsonschema.validate(instance=data, schema=schema)
            return True, None
        except jsonschema.ValidationError as e:
            return False, str(e.message)
        except Exception as e:
            return False, f"Schema validation error: {str(e)}"

    @abstractmethod
    def transform_to_django_format(self, data: dict) -> dict:
        """
        Transform JSON schema format to Django serializer format.

        This method must be implemented by subclasses to handle
        schema-specific field mappings.
        """
        pass

    @abstractmethod
    def extract_id(self, data: dict) -> Optional[str]:
        """
        Extract the ID field from the JSON data.

        Returns the natural key value (e.g., "z-example-1", "a-doris")
        """
        pass

    def get_existing_instance(self, natural_key: str) -> Optional[models.Model]:
        """Get existing model instance by natural key."""
        try:
            return self.model.objects.get(**{self.id_field: natural_key})
        except self.model.DoesNotExist:
            return None

    def import_single(
        self, data: dict, index: int = 0, validate_only: bool = False
    ) -> bool:
        """
        Import a single record.

        Returns:
            True if successful, False otherwise
        """
        record_id = self.extract_id(data)

        # Schema validation
        is_valid, error_msg = self.validate_schema(data)
        if not is_valid:
            self.result.errors.append(
                ImportError(
                    record_index=index,
                    record_id=record_id,
                    error_type="schema",
                    message=error_msg,
                )
            )
            self.result.failed += 1
            return False

        # Transform to Django format
        try:
            django_data = self.transform_to_django_format(data)
        except Exception as e:
            self.result.errors.append(
                ImportError(
                    record_index=index,
                    record_id=record_id,
                    error_type="transformation",
                    message=f"Data transformation error: {str(e)}",
                )
            )
            self.result.failed += 1
            return False

        # Check if update or create
        existing = None
        if record_id:
            existing = self.get_existing_instance(record_id)

        # Validate with serializer
        serializer = self.write_serializer(
            instance=existing, data=django_data, partial=bool(existing)
        )

        if not serializer.is_valid():
            errors = "; ".join(
                [f"{k}: {', '.join(v)}" for k, v in serializer.errors.items()]
            )
            self.result.errors.append(
                ImportError(
                    record_index=index,
                    record_id=record_id,
                    error_type="validation",
                    message=errors,
                )
            )
            self.result.failed += 1
            return False

        # If validate-only mode, stop here
        if validate_only:
            self.result.successful += 1
            return True

        # Save to database
        try:
            instance = serializer.save()
            actual_id = getattr(instance, self.id_field)

            if existing:
                self.result.updated_ids.append(actual_id)
            else:
                self.result.created_ids.append(actual_id)

            self.result.successful += 1
            return True

        except Exception as e:
            self.result.errors.append(
                ImportError(
                    record_index=index,
                    record_id=record_id,
                    error_type="database",
                    message=f"Database error: {str(e)}",
                )
            )
            self.result.failed += 1
            return False

    def import_batch(
        self,
        data_list: list[dict],
        atomic: bool = True,
        validate_only: bool = False,
    ) -> ImportResult:
        """
        Import multiple records.

        Args:
            data_list: List of JSON objects to import
            atomic: If True, rollback all changes on any error
            validate_only: If True, validate without saving to database

        Returns:
            ImportResult with success/failure details
        """
        self.result = ImportResult(total_records=len(data_list))

        if atomic and not validate_only:
            with transaction.atomic():
                for i, data in enumerate(data_list):
                    success = self.import_single(data, index=i, validate_only=False)
                    if not success and atomic:
                        raise Exception("Atomic import failed, rolling back")
        else:
            # Non-atomic: continue on errors
            for i, data in enumerate(data_list):
                self.import_single(data, index=i, validate_only=validate_only)

        return self.result
