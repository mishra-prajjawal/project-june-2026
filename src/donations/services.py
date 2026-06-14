from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from donations.models import Donation, DonationStatus, QualityFeedback
from events.signals import donation_claimed, donation_collected

def claim_donation(donation_id, ngo_user):
    """
    Claims an available donation for the given NGO.
    Uses select_for_update() row lock inside a transaction block to prevent race conditions.
    """
    if ngo_user.role != 'NGO':
        raise PermissionDenied("Only NGOs can claim donations.")
    if not ngo_user.is_verified:
        raise PermissionDenied("NGOs must be verified by an administrator to claim donations.")
    if ngo_user.is_banned:
        raise PermissionDenied("Banned accounts cannot claim donations.")

    with transaction.atomic():
        # Retrieve the donation and lock the row
        try:
            donation = Donation.objects.select_for_update().get(pk=donation_id)
        except Donation.DoesNotExist:
            raise ValueError("Donation does not exist.")
        
        # Enforce status constraint
        if donation.status != DonationStatus.AVAILABLE:
            raise ValueError("This donation has already been claimed by another NGO.")
            
        # Enforce expiration constraint
        if donation.expiry_time <= timezone.now():
            raise ValueError("This donation has expired and cannot be claimed.")
            
        # Update status
        donation.status = DonationStatus.CLAIMED
        donation.claimed_by = ngo_user
        donation.save()

    # Emit signal outside of the transaction block
    donation_claimed.send(sender=Donation, donation=donation, ngo=ngo_user)
    return donation

def confirm_collection(donation_id, ngo_user):
    """
    Confirms collection/pickup of a claimed food donation.
    """
    if ngo_user.role != 'NGO':
        raise PermissionDenied("Only NGOs can confirm collection.")
    if ngo_user.is_banned:
        raise PermissionDenied("Banned accounts cannot confirm collection.")

    with transaction.atomic():
        try:
            donation = Donation.objects.select_for_update().get(pk=donation_id)
        except Donation.DoesNotExist:
            raise ValueError("Donation does not exist.")
        
        # Enforce status constraint
        if donation.status != DonationStatus.CLAIMED:
            raise ValueError("This donation is not in a claimed state.")
            
        # Enforce claiming ownership constraint
        if donation.claimed_by != ngo_user:
            raise PermissionDenied("You can only confirm collection for donations that you claimed.")
            
        # Update status
        donation.status = DonationStatus.COLLECTED
        donation.collected_at = timezone.now()
        donation.save()

    # Emit signal outside of the transaction block
    donation_collected.send(sender=Donation, donation=donation, ngo=ngo_user)
    return donation

def record_quality_feedback(donation_id, ngo_user, acceptable):
    """
    Records a one-question quality survey after pickup/collection.
    """
    if ngo_user.role != 'NGO':
        raise PermissionDenied("Only NGOs can submit feedback.")

    with transaction.atomic():
        try:
            donation = Donation.objects.get(pk=donation_id)
        except Donation.DoesNotExist:
            raise ValueError("Donation does not exist.")
            
        # Enforce status constraint
        if donation.status != DonationStatus.COLLECTED:
            raise ValueError("Feedback can only be provided for collected donations.")
            
        # Enforce owner constraint
        if donation.claimed_by != ngo_user:
            raise PermissionDenied("You can only submit feedback for donations that you collected.")
            
        # Create or update feedback record
        feedback, created = QualityFeedback.objects.get_or_create(
            donation=donation,
            defaults={
                'ngo': ngo_user,
                'acceptable': acceptable
            }
        )
        if not created:
            feedback.acceptable = acceptable
            feedback.save()
            
    return feedback
