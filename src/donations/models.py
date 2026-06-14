from django.db import models
from django.conf import settings
from django.utils import timezone

class DonationStatus(models.TextChoices):
    AVAILABLE = 'Available', 'Available'
    CLAIMED = 'Claimed', 'Claimed'
    COLLECTED = 'Collected', 'Collected'

class Donation(models.Model):
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='donations_posted'
    )
    food_item = models.CharField(max_length=255, help_text="e.g. Rice and Curry")
    quantity = models.CharField(max_length=100, help_text="e.g. 5 kg / 30 servings")
    image = models.ImageField(upload_to='donation_images/', blank=True, null=True)
    expiry_time = models.DateTimeField(db_index=True, help_text="Best-before date and time")
    status = models.CharField(
        max_length=15,
        choices=DonationStatus.choices,
        default=DonationStatus.AVAILABLE,
        db_index=True
    )
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donations_claimed'
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    collected_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_expired(self):
        return self.expiry_time < timezone.now()

    def __str__(self):
        return f"{self.food_item} - {self.status}"


class Request(models.Model):
    """
    NGO request table.
    As per PROJECT_SPEC.md section 13 (Future Scope): The table must be created now,
    with minimal UI hook, but full rich workflow is deferred.
    """
    ngo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ngo_requests'
    )
    description = models.TextField(help_text="e.g. Need 50 packets Sunday")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request by {self.ngo.username} at {self.created_at}"


class QualityFeedback(models.Model):
    donation = models.OneToOneField(
        Donation,
        on_delete=models.CASCADE,
        related_name='quality_feedback'
    )
    ngo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_feedbacks'
    )
    acceptable = models.BooleanField(help_text="Was the food quality acceptable? Yes/No")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.donation.food_item} - Acceptable: {self.acceptable}"
