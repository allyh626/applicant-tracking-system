from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower

from .search import fold

DUPLICATE_EMAIL_MESSAGE = "A candidate with this email already exists."


class Skill(models.Model):
    """A skill that job openings can list as required (e.g. "Python")."""

    name = models.CharField(max_length=100)

    class Meta:
        # Alphabetical regardless of capitalisation ("django" before "SQL").
        ordering = [Lower("name")]
        constraints = [
            # "Python" and "python" count as the same skill.
            models.UniqueConstraint(
                Lower("name"),
                name="unique_skill_name_case_insensitive",
                violation_error_message="A skill with this name already exists.",
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Trim here (not only in forms) so every save path stores a clean name.
        self.name = self.name.strip()
        super().save(*args, **kwargs)


class Candidate(models.Model):
    """One person who may apply to job openings. One record per person (unique email)."""

    class Source(models.TextChoices):
        # Adding a source means a code change and a migration (a PRD decision).
        COMPANY_WEBSITE = "company_website", "Company Website"
        JOB_BOARD = "job_board", "Job Board"
        REFERRAL = "referral", "Referral"
        OTHER = "other", "Other"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    # Unique ignoring capitalisation: see the constraint in Meta.
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    source = models.CharField(max_length=20, choices=Source)
    source_details = models.CharField(
        max_length=200,
        blank=True,
        help_text="For example, which job board or who made the referral.",
    )
    notes = models.TextField(blank=True)
    profile_url = models.URLField("profile/resume URL", blank=True)
    # Archive and restore are built in Phase 9.
    archived = models.BooleanField(default=False)
    # Name and email, lowercased with accents removed, for the list search.
    # Filled in by save(), never typed. (A bulk QuerySet.update() skips save(),
    # so don't use one to change names or emails.)
    search_text = models.TextField(editable=False, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [Lower("last_name"), Lower("first_name")]
        constraints = [
            # "ana@example.com" and "Ana@Example.com" are the same person. The
            # email is still stored the way it was typed.
            models.UniqueConstraint(
                Lower("email"),
                name="unique_candidate_email_case_insensitive",
                violation_error_message=DUPLICATE_EMAIL_MESSAGE,
            ),
        ]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        # Trim here (not only in forms) so every save path stores clean values,
        # and " ana@example.com" can't slip past the unique email rule.
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()
        self.email = self.email.strip()
        self.search_text = self.build_search_text(self.first_name, self.last_name, self.email)
        super().save(*args, **kwargs)

    @staticmethod
    def build_search_text(first_name, last_name, email):
        return fold(f"{first_name} {last_name} {email}")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class JobOpening(models.Model):
    """A role the company is hiring for. Applications are attached to an opening."""

    title = models.CharField(max_length=200)
    # Free text on purpose: there is no Department model (out of scope).
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField()
    # New openings start open. Close and reopen only flip this flag. There is
    # no Draft status and no closed-at timestamp (PRD decisions).
    is_open = models.BooleanField("open", default=True)
    required_skills = models.ManyToManyField(Skill, blank=True, related_name="openings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [Lower("title"), "pk"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.title = self.title.strip()
        self.department = self.department.strip()
        self.location = self.location.strip()
        super().save(*args, **kwargs)


class Application(models.Model):
    """One candidate applying to one job opening, moving through the hiring stages."""

    class Stage(models.TextChoices):
        # In hiring order. The last three are final (Phase 7 adds the move rules).
        APPLIED = "applied", "Applied"
        SCREENING = "screening", "Screening"
        INTERVIEW = "interview", "Interview"
        FINAL_REVIEW = "final_review", "Final Review"
        OFFER = "offer", "Offer"
        HIRED = "hired", "Hired"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    # CASCADE: deleting a candidate (admin only) also deletes their applications.
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="applications")
    opening = models.ForeignKey(
        JobOpening,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name="job opening",
    )
    # Never set this directly once the application exists: Phase 7 adds the one
    # method that changes the stage and records who did it.
    stage = models.CharField(max_length=20, choices=Stage, default=Stage.APPLIED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "opening"],
                name="unique_application_per_candidate_and_opening",
            ),
        ]

    def __str__(self):
        return f"{self.candidate} → {self.opening}"

    def unique_error_message(self, model_class, unique_check):
        # Django calls this when the candidate/opening constraint is broken. It
        # replaces the default "Application with this Candidate and Job opening
        # already exists." with one that names the person and the role, in the
        # app's form and in the admin alike.
        if set(unique_check) == {"candidate", "opening"}:
            return ValidationError(
                f"{self.candidate} has already applied to {self.opening}.",
                code="unique_together",
            )
        return super().unique_error_message(model_class, unique_check)
