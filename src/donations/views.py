from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from accounts.models import UserRole, User
from donations.models import Donation, DonationStatus
from donations.forms import DonationPostForm
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
    Dashboard for NGOs to browse and claim active donations.
    """
    if request.user.role != UserRole.NGO:
        raise PermissionDenied("Only NGOs can access the NGO dashboard.")
    
    # Stub response to be completed in Slice 4
    return HttpResponse("NGO Dashboard Stub")
