from django.db import models
from django.db.models.functions import Lower


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
