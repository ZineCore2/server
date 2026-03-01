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


class ProfileAgentClaim(TimestampedModel):
    """A profile's claim on an agent record with approval workflow."""

    class ClaimStatus(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    profile = models.ForeignKey(
        "Profile",
        on_delete=models.CASCADE,
        related_name="agent_claims",
    )
    agent = models.ForeignKey(
        "agents.Agent",
        on_delete=models.CASCADE,
        related_name="profile_claims",
    )
    status = models.CharField(
        max_length=20,
        choices=ClaimStatus.choices,
        default=ClaimStatus.REQUESTED,
        help_text="Approval status of this claim",
    )
    note = models.TextField(
        blank=True,
        default="",
        help_text="Notes about this claim (reason, approval notes, etc.)",
    )

    class Meta:
        db_table = "profile_agent_claims"
        verbose_name = "Profile Agent Claim"
        verbose_name_plural = "Profile Agent Claims"
        unique_together = [["profile", "agent"]]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile.user.username} → {self.agent.display_name} ({self.status})"


class ProfileRepositoryClaim(TimestampedModel):
    """A profile's claim on a repository with approval workflow."""

    class ClaimStatus(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    profile = models.ForeignKey(
        "Profile",
        on_delete=models.CASCADE,
        related_name="repository_claims",
    )
    repository = models.ForeignKey(
        "repositories.Repository",
        on_delete=models.CASCADE,
        related_name="profile_claims",
    )
    status = models.CharField(
        max_length=20,
        choices=ClaimStatus.choices,
        default=ClaimStatus.REQUESTED,
        help_text="Approval status of this claim",
    )
    note = models.TextField(
        blank=True,
        default="",
        help_text="Notes about this claim (reason, approval notes, etc.)",
    )

    class Meta:
        db_table = "profile_repository_claims"
        verbose_name = "Profile Repository Claim"
        verbose_name_plural = "Profile Repository Claims"
        unique_together = [["profile", "repository"]]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile.user.username} → {self.repository.name} ({self.status})"


class Profile(TimestampedModel):
    """User profile with optional agent and repository associations via claims."""

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
    agents = models.ManyToManyField(
        "agents.Agent",
        through="ProfileAgentClaim",
        related_name="profiles",
        help_text="Agents this profile has claims on",
    )
    repositories = models.ManyToManyField(
        "repositories.Repository",
        through="ProfileRepositoryClaim",
        related_name="profiles",
        help_text="Repositories this profile has claims on",
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
