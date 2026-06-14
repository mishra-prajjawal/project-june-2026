import re
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from accounts.models import User, UserRole
from donations.models import Donation, DonationStatus

def home(request):
    """
    Renders the public landing page with donor leaderboard and basic impact stats.
    """
    # 1. Fetch top donors ranked by impact score, resolved by creation date for tie-breaks
    leaderboard = User.objects.filter(
        role=UserRole.DONOR,
        impact_score__gt=0
    ).order_by('-impact_score', 'created_at')[:10]

    # 2. Compute aggregate metrics
    total_users_count = User.objects.exclude(role=UserRole.ADMIN).count()
    
    collected_donations = Donation.objects.filter(status=DonationStatus.COLLECTED)
    total_servings = 0
    for d in collected_donations:
        match = re.search(r'\d+', d.quantity)
        if match:
            total_servings += int(match.group())
        else:
            total_servings += 10 # Default fallback

    context = {
        'leaderboard': leaderboard,
        'metrics': {
            'total_servings': total_servings,
            'active_rescuers': total_users_count,
        }
    }
    return render(request, 'core/home.html', context)

@login_required
def admin_panel(request):
    """
    Oversight dashboard for NGO verification, user bans, and metrics.
    """
    if request.user.role != UserRole.ADMIN:
        raise PermissionDenied("Only administrators can access the admin dashboard.")

    # Search keyword for user directory list
    q = request.GET.get('q', '').strip()

    # 1. Fetch unverified NGOs for the approval queue
    pending_ngos = User.objects.filter(role=UserRole.NGO, is_verified=False).order_by('created_at')

    # 2. Fetch all other users for the user management directory
    users = User.objects.exclude(id=request.user.id).order_by('-created_at')
    if q:
        users = users.filter(
            username__icontains=q
        ) | users.filter(
            email__icontains=q
        ) | users.filter(
            contact_info__icontains=q
        )

    # 3. Calculate system-wide summary metrics
    total_users = User.objects.count()
    pending_verifications = pending_ngos.count()
    active_donations = Donation.objects.filter(status=DonationStatus.AVAILABLE).count()
    banned_accounts = User.objects.filter(is_banned=True).count()

    # Compute total servings rescued (database-agnostic string parsing in Python)
    collected_donations = Donation.objects.filter(status=DonationStatus.COLLECTED)
    total_servings = 0
    for d in collected_donations:
        match = re.search(r'\d+', d.quantity)
        if match:
            total_servings += int(match.group())
        else:
            total_servings += 10 # Default fallback

    context = {
        'pending_ngos': pending_ngos,
        'users': users,
        'q': q,
        'metrics': {
            'total_users': total_users,
            'pending_verifications': pending_verifications,
            'active_donations': active_donations,
            'banned_accounts': banned_accounts,
            'total_servings': total_servings,
        }
    }
    
    return render(request, 'core/admin_panel.html', context)

def handler404(request, exception):
    """
    Custom handler for 404 (Page Not Found) errors.
    """
    return render(request, '404.html', status=404)

def handler500(request):
    """
    Custom handler for 500 (Internal Server Error) errors.
    """
    return render(request, '500.html', status=500)
