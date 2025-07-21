# forms.py
from django import forms
from .models import OffSiteItem

class OffSiteItemForm(forms.ModelForm):
    class Meta:
        model = OffSiteItem
        fields = ['item_no', 'name', 'item_type', 'predefined_replies']
        widgets = {
            'name': forms.Textarea(attrs={'rows': 6}), # Make 'name' a textarea
            'predefined_replies': forms.Textarea(attrs={'rows': 10}), # Ensure this is also a textarea
        }
