from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from accounts.forms import FoodConnectRegistrationForm
from accounts.models import UserRole

def register(request):
    """
    Handles donor and NGO user registration.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = FoodConnectRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')
    else:
        form = FoodConnectRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def dashboard(request):
    """
    Role-aware router redirecting users to their respective workspace dashboards.
    Enforces bans at entry point.
    """
    # Verify ban state
    if request.user.is_banned:
        logout(request)
        messages.error(request, 'Your account has been banned by an administrator.')
        return redirect('login')

    if request.user.role == UserRole.ADMIN:
        return redirect('core:admin_panel')
    elif request.user.role == UserRole.DONOR:
        return redirect('donations:donor_dashboard')
    elif request.user.role == UserRole.NGO:
        return redirect('donations:ngo_dashboard')

    return redirect('core:home')
