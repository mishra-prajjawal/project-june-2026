from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from accounts.models import UserRole

User = get_user_model()

class FoodConnectRegistrationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[(UserRole.DONOR.value, 'Food Donor (Restaurant, Hotel, Venue)'),
                 (UserRole.NGO.value, 'Recipient NGO / Volunteer Organization')],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 bg-brand-slate border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-brand-green/45 focus:ring-1 focus:ring-brand-green/45 transition',
            'onchange': 'toggleDocumentUpload(this.value)'
        }),
        label="I want to register as a"
    )
    
    contact_info = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Primary phone number (e.g. +1 555-0199)',
            'class': 'w-full px-4 py-3 bg-brand-slate border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-brand-green/45 focus:ring-1 focus:ring-brand-green/45 transition'
        }),
        label="Contact Number / Info"
    )

    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Physical address (for pickup/coordination)',
            'rows': 3,
            'class': 'w-full px-4 py-3 bg-brand-slate border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-brand-green/45 focus:ring-1 focus:ring-brand-green/45 transition'
        }),
        required=True,
        label="Physical Address"
    )

    verification_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-brand-green-light file:text-brand-green-dark hover:file:bg-brand-green-light/80 file:cursor-pointer'
        }),
        label="Verification Document (NGO Registration Certificate / ID)"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('role', 'contact_info', 'address', 'verification_document')

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        verification_document = cleaned_data.get('verification_document')

        # If registering as NGO, verification document is strictly required
        if role == UserRole.NGO.value and not verification_document:
            self.add_error('verification_document', 'NGO registration requires uploading a verification document.')
        
        return cleaned_data
