from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import PermissionDenied
from accounts.models import User, UserRole
from events.signals import ngo_verified, user_banned

def verify_ngo_user(ngo_id, admin_user):
    """
    Approve an NGO registration. Sets is_verified to True and fires a signal.
    """
    if admin_user.role != UserRole.ADMIN:
        raise PermissionDenied("Only administrators can verify NGOs.")

    with transaction.atomic():
        ngo_user = User.objects.select_for_update().get(pk=ngo_id)
        if ngo_user.role != UserRole.NGO:
            raise ValueError("User is not an NGO.")
        
        ngo_user.is_verified = True
        ngo_user.save()

    # Trigger internal event bus signal (outside atomic block to avoid SSE blocking transaction)
    ngo_verified.send(sender=User, ngo_user=ngo_user, admin_user=admin_user)
    return ngo_user

def reject_ngo_user(ngo_id, admin_user):
    """
    Reject an NGO registration. Deletes the user profile so they can re-register 
    with corrected documents.
    """
    if admin_user.role != UserRole.ADMIN:
        raise PermissionDenied("Only administrators can reject NGOs.")

    with transaction.atomic():
        ngo_user = User.objects.select_for_update().get(pk=ngo_id)
        if ngo_user.role != UserRole.NGO:
            raise ValueError("User is not an NGO.")
        
        # Delete the verification document file if it exists
        if ngo_user.verification_document:
            ngo_user.verification_document.delete(save=False)
            
        ngo_user.delete()
    return None

def toggle_user_ban(user_id, admin_user):
    """
    Toggle a user's banned status. If banned, they are blocked from using the platform.
    Fires a signal if user is banned.
    """
    if admin_user.role != UserRole.ADMIN:
        raise PermissionDenied("Only administrators can ban/unban users.")

    if int(user_id) == admin_user.id:
        raise ValueError("Administrators cannot ban themselves.")

    with transaction.atomic():
        target_user = User.objects.select_for_update().get(pk=user_id)
        target_user.is_banned = not target_user.is_banned
        target_user.save()

    if target_user.is_banned:
        user_banned.send(sender=User, target_user=target_user, admin_user=admin_user)
        
    return target_user
