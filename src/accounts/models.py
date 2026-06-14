from django.db import models
from django.contrib.auth.models import AbstractUser

class UserRole(models.TextChoices):
    DONOR = 'Donor', 'Donor'
    NGO = 'NGO', 'NGO'
    ADMIN = 'Admin', 'Admin'

class User(AbstractUser):
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.DONOR
    )
    contact_info = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Primary phone number and/or alternative email"
    )
    address = models.TextField(
        blank=True,
        help_text="Physical address for coordination"
    )
    is_verified = models.BooleanField(
        default=False, 
        help_text="NGOs start false until approved by an admin; Donors/Admins are auto-verified"
    )
    is_banned = models.BooleanField(
        default=False,
        help_text="Banned users are blocked from taking actions"
    )
    impact_score = models.IntegerField(
        default=0,
        help_text="Gamification score tracking total contributions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For NGO verification documents
    verification_document = models.FileField(
        upload_to='verification_documents/', 
        blank=True, 
        null=True,
        help_text="Registration or tax document uploaded by NGO"
    )

    def save(self, *args, **kwargs):
        # Auto-verify Donors and Admins on first creation
        if self.role in [UserRole.DONOR, UserRole.ADMIN]:
            self.is_verified = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"
