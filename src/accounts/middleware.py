from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect

class BannedUserMiddleware:
    """
    Middleware that checks if an authenticated user has been banned.
    If so, immediately terminates their active session, logs them out,
    and redirects them to the login page with a notice.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_banned:
            logout(request)
            messages.error(request, 'Your account has been banned by an administrator.')
            return redirect('login')
        return self.get_response(request)
