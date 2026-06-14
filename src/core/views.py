from django.shortcuts import render

def home(request):
    """
    Renders the public landing page with donor leaderboard and basic impact stats.
    """
    # We will build the leaderboard query in Phase 1, slice 5. For now, render basic landing.
    return render(request, 'core/home.html')
