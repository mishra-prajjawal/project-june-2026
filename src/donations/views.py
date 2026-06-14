from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@login_required
def donor_dashboard(request):
    """
    Dashboard for donors to post food and track status.
    """
    # Stub response to be completed in Slice 3
    return HttpResponse("Donor Dashboard Stub")

@login_required
def ngo_dashboard(request):
    """
    Dashboard for NGOs to browse and claim active donations.
    """
    # Stub response to be completed in Slice 4
    return HttpResponse("NGO Dashboard Stub")
