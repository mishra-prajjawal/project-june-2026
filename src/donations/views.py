from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from accounts.models import UserRole, User
from donations.models import Donation, DonationStatus
from donations.forms import DonationPostForm
from donations import services as donations_services
from events.signals import donation_posted

@login_required
def donor_dashboard(request):
    """
    Dashboard for donors to view impact stats, leaderboard rank,
    active listings, and donation history.
    """
    if request.user.role != UserRole.DONOR:
        raise PermissionDenied("Only donors can access the donor dashboard.")

    # Calculate leaderboard rank (ordered by impact_score, then created_at)
    donors = User.objects.filter(role=UserRole.DONOR).order_by('-impact_score', 'created_at')
    leaderboard_rank = 1
    for idx, d in enumerate(donors):
        if d.id == request.user.id:
            leaderboard_rank = idx + 1
            break

    # Active donations (Available or Claimed)
    active_donations = Donation.objects.filter(
        donor=request.user
    ).exclude(
        status=DonationStatus.COLLECTED
    ).order_by('-created_at')

    # Past donations (Collected)
    past_donations = Donation.objects.filter(
        donor=request.user,
        status=DonationStatus.COLLECTED
    ).order_by('-collected_at')

    context = {
        'leaderboard_rank': leaderboard_rank,
        'active_donations': active_donations,
        'past_donations': past_donations,
    }
    
    return render(request, 'donations/donor_dashboard.html', context)

@login_required
def post_donation(request):
    """
    Saves a food donation post form, fires the creation signal,
    and displays the animated success green checkmark template.
    """
    if request.user.role != UserRole.DONOR:
        raise PermissionDenied("Only donors can post food donations.")

    if request.method == 'POST':
        form = DonationPostForm(request.POST, request.FILES)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = request.user
            donation.status = DonationStatus.AVAILABLE
            donation.save()

            # Fire signal to trigger notifications and live feed update via SSE
            donation_posted.send(sender=Donation, donation=donation)

            return render(request, 'donations/post_success.html', {'donation': donation})
    else:
        form = DonationPostForm()

    return render(request, 'donations/post_donation.html', {'form': form})

@login_required
def ngo_dashboard(request):
    """
    Dashboard for Recipient NGOs to browse available donations,
    manage current claims, and confirm pickups.
    """
    if request.user.role != UserRole.NGO:
        raise PermissionDenied("Only Recipient NGOs can access the NGO dashboard.")

    # 1. Fetch available donations that are not expired (ordered by expiry_time)
    now = timezone.now()
    available_donations = Donation.objects.filter(
        status=DonationStatus.AVAILABLE,
        expiry_time__gt=now
    ).order_by('expiry_time')

    # 2. Fetch current active claims claimed by this NGO
    my_claims = Donation.objects.filter(
        status=DonationStatus.CLAIMED,
        claimed_by=request.user
    ).order_by('-created_at')

    # 3. Fetch past collected history by this NGO
    my_history = Donation.objects.filter(
        status=DonationStatus.COLLECTED,
        claimed_by=request.user
    ).order_by('-collected_at')

    context = {
        'available_donations': available_donations,
        'my_claims': my_claims,
        'my_history': my_history,
    }
    
    return render(request, 'donations/ngo_dashboard.html', context)

@login_required
def claim_donation_view(request, donation_id):
    """
    POST endpoint to trigger a claim on a donation.
    """
    if request.user.role != UserRole.NGO:
        raise PermissionDenied("Only NGOs can claim donations.")

    if request.method == 'POST':
        try:
            donations_services.claim_donation(donation_id, request.user)
            messages.success(request, "Donation claimed successfully! Contact details revealed below.")
        except (ValueError, PermissionDenied) as e:
            messages.error(request, str(e))

    return redirect('donations:ngo_dashboard')
