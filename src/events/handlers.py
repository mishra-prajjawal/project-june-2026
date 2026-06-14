import re
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from events.signals import donation_posted, donation_claimed, donation_collected, ngo_verified, user_banned
from events.sse import sse_manager

def parse_servings_from_quantity(quantity_str):
    """
    Helper to extract a numeric serving count from a quantity string.
    e.g. '30 servings' -> 30, '5 kg' -> 5, 'Rice' -> 10 (default).
    """
    match = re.search(r'\d+', quantity_str)
    if match:
        return int(match.group())
    return 10  # Fallback default score points

@receiver(donation_posted)
def handle_donation_posted(sender, donation, **kwargs):
    data = {
        'donation_id': donation.id,
        'food_item': donation.food_item,
        'quantity': donation.quantity,
        'expiry_time': donation.expiry_time.isoformat() if donation.expiry_time else None,
        'address': donation.address,
        'status': donation.status,
        'donor_name': donation.donor.username,
        'created_at': donation.created_at.isoformat() if donation.created_at else None,
    }
    sse_manager.broadcast(data, event_type='donation_posted')

@receiver(donation_claimed)
def handle_donation_claimed(sender, donation, ngo, **kwargs):
    data = {
        'donation_id': donation.id,
        'food_item': donation.food_item,
        'status': donation.status,
        'claimed_by': ngo.username,
        'contact_info': donation.donor.contact_info,
    }
    sse_manager.broadcast(data, event_type='donation_claimed')

@receiver(donation_collected)
def handle_donation_collected(sender, donation, ngo, **kwargs):
    donor = donation.donor
    servings = parse_servings_from_quantity(donation.quantity)
    points_to_add = max(10, servings)

    # Atomically award impact score points to the donor
    with transaction.atomic():
        from accounts.models import User
        db_donor = User.objects.select_for_update().get(pk=donor.pk)
        db_donor.impact_score += points_to_add
        db_donor.save()

    data = {
        'donation_id': donation.id,
        'food_item': donation.food_item,
        'status': donation.status,
        'collected_at': donation.collected_at.isoformat() if donation.collected_at else None,
        'donor_id': donor.id,
        'donor_name': donor.username,
        'donor_impact_score': db_donor.impact_score,
    }
    sse_manager.broadcast(data, event_type='donation_collected')

@receiver(ngo_verified)
def handle_ngo_verified(sender, ngo_user, **kwargs):
    data = {
        'ngo_id': ngo_user.id,
        'ngo_name': ngo_user.username,
        'is_verified': ngo_user.is_verified,
    }
    sse_manager.broadcast(data, event_type='ngo_verified')

@receiver(user_banned)
def handle_user_banned(sender, target_user, **kwargs):
    data = {
        'user_id': target_user.id,
        'username': target_user.username,
        'is_banned': target_user.is_banned,
    }
    sse_manager.broadcast(data, event_type='user_banned')
