
from django import forms
from .models import AuditSubmission, AuditObjection, Person, Comment, Upload, Personel_Decision, Items, ObjectionDecision
from django.forms import  widgets



class AuditSubmissionForm(forms.ModelForm):
    class Meta:
        model = AuditSubmission
        fields = ['branch', 'start_date', 'end_date', 'year_range', 'audit_type']

        widgets = {
            'start_date': widgets.DateInput(attrs={'type': 'date'}),
            'end_date': widgets.DateInput(attrs={'type': 'date'})
        }
class AuditObjectionForm(forms.ModelForm):


    description = forms.CharField(
        widget=forms.Textarea(attrs={'id': 'id_description'}),  # Explicitly set Textarea widget
        required=False,
        label="Description"  # Ensure label is set correctly
    )


    class Meta:
        model = AuditObjection
        fields = ['items', 'description', 'amount', 'category']



class LoginForm(forms.Form):
        username = forms.EmailField(label='Email')
        password = forms.CharField(widget=forms.PasswordInput)

class CommentForm(forms.ModelForm):
    parent_id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Comment
        fields = ['comment', 'file', 'parent_id']

    def clean(self):
        cleaned_data = super().clean()
        comment = cleaned_data.get("comment")
        file = cleaned_data.get("file")

        if not comment and not file:
            raise forms.ValidationError("Please provide a comment or attach a file.")

        return cleaned_data



class UploadForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = ['file_description', 'document']
        widgets = {
            'file_description': forms.TextInput(attrs={'class': 'form-control'}),
            'document': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        document = cleaned_data.get("document")

        # Allow empty document if editing, but enforce for new entries
        if not self.instance.pk and not document:
            raise forms.ValidationError("Please upload a file.")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only require document if the form is for a new file
        if self.instance and self.instance.pk:
            self.fields['document'].required = False
            self.fields['file_description'].required = False


class Personel_DecisionForm(forms.ModelForm):
    isEmployee_involve = forms.BooleanField(
        required=False,
        widget=forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
        label="Do you want to fill out the employee form?"
    )

    class Meta:
        model = Personel_Decision
        fields = ['isEmployee_involve']


    def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields['isEmployee_involve'].required = False


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['name', 'pf', 'accused_time_post', 'current_post', 'accusing_time', 'accusing_tenure', 'accusing_time_branch', 'current_branch']


        widgets = {

            'accusing_time': forms.DateInput(attrs={'type': 'date'})
        }


class ItemForm(forms.ModelForm):
    class Meta:
        model = Items
        fields = ['itemNo','itemName', 'category']

class ObjectionDecisionForm(forms.ModelForm):
    class Meta:
        model = ObjectionDecision
        fields = ['decision']
        widgets = {
            'decision': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['decision'].label = "Admin Decision"
        self.fields['decision'].choices = ObjectionDecision._meta.get_field('decision').choices
        self.fields['decision'].help_text = "Choose 'Close' to prevent further comments by regular users."





