from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from accounts.forms import FoodConnectRegistrationForm
from accounts.models import User, UserRole
from accounts import services as accounts_services

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
    Role-aware router redirecting users to their respective dashboards.
    """
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

@login_required
def verify_ngo(request, user_id):
    """
    Action endpoint to approve/verify an NGO account.
    """
    if request.user.role != UserRole.ADMIN:
        raise PermissionDenied("Only administrators can verify NGOs.")
    
    if request.method == 'POST':
        accounts_services.verify_ngo_user(user_id, request.user)
        messages.success(request, "NGO has been successfully verified.")
        
    return redirect('core:admin_panel')

@login_required
def reject_ngo(request, user_id):
    """
    Action endpoint to reject/delete an NGO account.
    """
    if request.user.role != UserRole.ADMIN:
        raise PermissionDenied("Only administrators can reject NGOs.")
    
    if request.method == 'POST':
        accounts_services.reject_ngo_user(user_id, request.user)
        messages.success(request, "NGO registration has been rejected.")
        
    return redirect('core:admin_panel')

@login_required
def toggle_ban(request, user_id):
    """
    Action endpoint to toggle a user's banned status.
    """
    if request.user.role != UserRole.ADMIN:
        raise PermissionDenied("Only administrators can toggle bans.")
    
    if request.method == 'POST':
        try:
            target = accounts_services.toggle_user_ban(user_id, request.user)
            action_str = "banned" if target.is_banned else "unbanned"
            messages.success(request, f"User {target.username} has been successfully {action_str}.")
        except ValueError as e:
            messages.error(request, str(e))
            
    return redirect('core:admin_panel')
