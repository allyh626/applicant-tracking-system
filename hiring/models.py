from itertools import pairwise

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.functions import Lower
from django.utils import timezone

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


class StageMoveError(Exception):
    """Raised by Application.move_to() when a move breaks the stage rules."""


class Application(models.Model):
    """One candidate applying to one job opening, moving through the hiring stages."""

    class Stage(models.TextChoices):
        # In hiring order. The last three are final: see ALLOWED_MOVES below.
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
    # Never set this directly once the application exists: use move_to(), which
    # checks the rules and records who made the change.
    stage = models.CharField(max_length=20, choices=Stage, default=Stage.APPLIED)
    # When the stage last changed (the pipeline shows it). Set on creation and
    # by move_to(). Separate from updated_at, which changes on any edit.
    stage_changed_at = models.DateTimeField(default=timezone.now, editable=False)
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

    def allowed_moves(self):
        """The stages this application may move to next (empty when final)."""
        return ALLOWED_MOVES[self.stage]

    @property
    def is_final(self):
        return not self.allowed_moves()

    def move_to(self, new_stage, user):
        """The one way to change the stage: check the rules, move, and record it.

        The stage update and the StageChange row are written together, or
        neither is. Raises StageMoveError (and writes nothing) if the move
        isn't allowed. Returns the new StageChange.
        """
        if new_stage not in self.allowed_moves():
            raise StageMoveError(self._refusal_message(new_stage))
        old_stage = self.stage
        now = timezone.now()
        with transaction.atomic():
            # Update only if the stage in the database is still the one we
            # checked. If a colleague moved it a moment ago, nothing matches,
            # and the move is refused instead of being recorded twice.
            moved = Application.objects.filter(pk=self.pk, stage=old_stage).update(
                stage=new_stage, stage_changed_at=now, updated_at=now
            )
            if not moved:
                # Only the stage fields, so the cached candidate and opening stay.
                self.refresh_from_db(fields=["stage", "stage_changed_at", "updated_at"])
                raise StageMoveError(
                    f"Someone else just moved this application to "
                    f"{self.get_stage_display()}. Check its stage and try again."
                )
            change = StageChange.objects.create(
                application=self,
                from_stage=old_stage,
                to_stage=new_stage,
                changed_by=user,
                changed_at=now,
            )
        self.stage = new_stage
        self.stage_changed_at = self.updated_at = now
        return change

    def _refusal_message(self, new_stage):
        current = self.get_stage_display()
        if self.is_final:
            return f"This application is already {current}, which is final."
        # .get(): a crafted request can send any text, not just a real stage.
        target = dict(self.Stage.choices).get(new_stage, new_stage)
        return f"Can't move from {current} to {target}."


# The stage rules, all in one place: each stage maps to the stages it may move
# to. One step forward at a time; Reject or Withdraw from any stage that isn't
# final; Hired, Rejected and Withdrawn allow no moves (so no going backwards).
_Stage = Application.Stage
_FORWARD = [
    _Stage.APPLIED,
    _Stage.SCREENING,
    _Stage.INTERVIEW,
    _Stage.FINAL_REVIEW,
    _Stage.OFFER,
    _Stage.HIRED,
]
ALLOWED_MOVES = {
    **{
        stage: [next_stage, _Stage.REJECTED, _Stage.WITHDRAWN]
        for stage, next_stage in pairwise(_FORWARD)
    },
    _Stage.HIRED: [],
    _Stage.REJECTED: [],
    _Stage.WITHDRAWN: [],
}


class StageChange(models.Model):
    """One stage move, kept forever: who moved which application, from where to where, when.

    Append-only: rows are written by Application.move_to() and never edited.
    """

    # CASCADE: deleting a candidate in the admin deletes their history too.
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="stage_changes"
    )
    from_stage = models.CharField(max_length=20, choices=Application.Stage)
    to_stage = models.CharField(max_length=20, choices=Application.Stage)
    # PROTECT: a staff account with recorded decisions can't be deleted (it
    # can still be deactivated in the admin), so the history keeps its names.
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stage_changes"
    )
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["changed_at", "pk"]

    def __str__(self):
        return (
            f"{self.application}: {self.get_from_stage_display()} → {self.get_to_stage_display()}"
        )
