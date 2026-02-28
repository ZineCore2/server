from django.contrib.auth import get_user_model
from django.db import models

from core.models import BaseVocabulary, TimestampedModel

User = get_user_model()


class SubmissionStatus(BaseVocabulary):
    """Controlled vocabulary for zine submission status."""

    class Meta(BaseVocabulary.Meta):
        db_table = "submission_statuses"
        verbose_name = "Submission Status"
        verbose_name_plural = "Submission Statuses"


class Profile(TimestampedModel):
    """User profile with optional agent and repository associations."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        primary_key=True,
    )
    profile_image = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
        help_text="Profile image",
    )
    agent = models.ForeignKey(
        "agents.Agent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profiles",
        help_text="Link to agent record (e.g., 'this is me')",
    )
    repository = models.ForeignKey(
        "repositories.Repository",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profiles",
        help_text="Link to repository (e.g., 'I'm associated with this repo')",
    )

    class Meta:
        db_table = "profiles"
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return f"Profile for {self.user.username}"


class ZineSubmission(TimestampedModel):
    """Tracks a user's submission of a zine to a repository."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    zine = models.ForeignKey(
        "catalog.Zine",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    repository = models.ForeignKey(
        "repositories.Repository",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    status = models.ForeignKey(
        SubmissionStatus,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes about the submission",
    )
    send_digital = models.BooleanField(
        default=False,
        help_text="Send digital copy of the zine",
    )
    send_print = models.BooleanField(
        default=False,
        help_text="Send print copy of the zine",
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the submission was made (auto-populated when status changes to 'submitted')",
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the repository responded (auto-populated when status changes to 'accepted' or 'rejected')",
    )

    class Meta:
        db_table = "zine_submissions"
        verbose_name = "Zine Submission"
        verbose_name_plural = "Zine Submissions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} → {self.zine.title} → {self.repository.name} ({self.status})"
