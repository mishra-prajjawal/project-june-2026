from django import forms
from django.utils import timezone
from donations.models import Donation

class DonationPostForm(forms.ModelForm):
    expiry_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'w-full px-4 py-3 bg-brand-slate border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-brand-green/45 focus:ring-1 focus:ring-brand-green/45 transition'
        }),
        label="Best-Before / Expiry Time"
    )
    
    latitude = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    longitude = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False
    )

    class Meta:
        model = Donation
        fields = ['food_item', 'quantity', 'image', 'expiry_time', 'address', 'latitude', 'longitude']
        widgets = {
            'food_item': forms.TextInput(attrs={
                'placeholder': 'e.g. Rice and Curry, Veg Sandwiches',
                'class': 'w-full px-4 py-3 bg-brand-slate border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-brand-green/45 focus:ring-1 focus:ring-brand-green/45 transition'
            }),
            'quantity': forms.TextInput(attrs={
                'placeholder': 'e.g. 30 servings, 5 kg',
                'class': 'w-full px-4 py-3 bg-brand-slate border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-brand-green/45 focus:ring-1 focus:ring-brand-green/45 transition'
            }),
            'address': forms.Textarea(attrs={
                'placeholder': 'Pickup address (include land mark if any)',
                'rows': 3,
                'class': 'w-full px-4 py-3 bg-brand-slate border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-brand-green/45 focus:ring-1 focus:ring-brand-green/45 transition'
            }),
            'image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-brand-green-light file:text-brand-green-dark hover:file:bg-brand-green-light/80 file:cursor-pointer'
            }),
        }

    def clean_expiry_time(self):
        expiry_time = self.cleaned_data.get('expiry_time')
        # Expiry time must be in the future
        if expiry_time and expiry_time <= timezone.now():
            raise forms.ValidationError("The best-before time must be in the future.")
        return expiry_time

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity', '').strip()
        if not quantity:
            raise forms.ValidationError("Quantity is required.")
        return quantity
