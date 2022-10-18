from django import forms
from django.forms import widgets
from .models import *
from django.contrib.auth.models import User


class UserProfilesForm(forms.ModelForm):
    class Meta:
        model = UserProfiles
        fields = '__all__'

        widgets = {
            'branch': forms.Select(attrs={'class': 'form-control form-control-select2', 'required': 'True', 'name': 'apartment', 'placeholder': 'Branch'}),
        }


class BorrowersProfile(forms.ModelForm):
    class Meta:
        model = Borrowers
        fields = '__all__'

        widgets = {
            'branch': forms.Select(attrs={'class': 'form-control form-control-select2', 'required': 'True', 'name': 'apartment', 'placeholder': 'Branch'}),
            'loan_officer': forms.Select(attrs={'class': 'form-control form-control-select2', 'required': 'True', 'name': 'apartment', 'placeholder': 'Loan Officer'}),
            'loan_collection_officer': forms.Select(attrs={'class': 'form-control form-control-select2', 'required': 'True', 'name': 'apartment', 'placeholder': 'Loan Collection Officer'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['loan_officer'].queryset = UserProfiles.objects.filter(
            role="Loan Officer")
        self.fields['loan_collection_officer'].queryset = UserProfiles.objects.filter(
            role="Loan Collection Officer")
