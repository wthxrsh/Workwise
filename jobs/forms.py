from django import forms

from .models import Job


class Jobform(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company_name', 'description', 'location', 'salary']
        labels = {'salary': 'Annual salary (₹)'}
        help_texts = {'salary': 'Enter the yearly salary in Indian rupees.'}
        widgets = {
            'salary': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }


class ApplicationForm(forms.Form):
    resume = forms.FileField(
        label="Resume (PDF)",
        help_text="Upload a PDF file, up to 10 MB.",
    )

    def clean_resume(self):
        resume = self.cleaned_data["resume"]
        if not resume.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Upload your resume as a PDF file.")
        if resume.size > 10 * 1024 * 1024:
            raise forms.ValidationError("The PDF must be 10 MB or smaller.")
        if resume.read(5) != b"%PDF-":
            raise forms.ValidationError("The uploaded file is not a valid PDF.")
        resume.seek(0)
        return resume