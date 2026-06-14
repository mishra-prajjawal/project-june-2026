from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

def home(request):
    """
    Renders the public landing page with donor leaderboard and basic impact stats.
    """
    return render(request, 'core/home.html')

@login_required
def admin_panel(request):
    """
    Oversight dashboard for NGO verification, user bans, and metrics.
    """
    # Stub response to be completed in Slice 2
    return HttpResponse("Admin Panel Stub")
