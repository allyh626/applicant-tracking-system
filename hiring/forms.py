from django import forms

from .models import DUPLICATE_EMAIL_MESSAGE, Candidate, Skill


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input w-full", "placeholder": "e.g. Python"}),
        }


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "source",
            "source_details",
            "profile_url",
            "notes",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "input w-full"}),
            "last_name": forms.TextInput(attrs={"class": "input w-full"}),
            "email": forms.EmailInput(attrs={"class": "input w-full"}),
            "phone": forms.TextInput(attrs={"class": "input w-full"}),
            "source": forms.Select(attrs={"class": "select w-full"}),
            "source_details": forms.TextInput(attrs={"class": "input w-full"}),
            "profile_url": forms.URLInput(
                attrs={"class": "input w-full", "placeholder": "https://"}
            ),
            "notes": forms.Textarea(attrs={"class": "textarea w-full", "rows": 4}),
        }

    def clean_email(self):
        # The database constraint would also catch a duplicate, but its error
        # isn't tied to a field. Checking here shows it under the Email box.
        email = self.cleaned_data["email"]
        others = Candidate.objects.exclude(pk=self.instance.pk)
        if others.filter(email__iexact=email).exists():
            raise forms.ValidationError(DUPLICATE_EMAIL_MESSAGE)
        return email
