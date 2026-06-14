"""
URL configuration for foodconnect project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", accounts_views.dashboard, name="dashboard"),
    
    path("auth/", include("accounts.urls")),
    path("donations/", include("donations.urls")),
    path("events/", include("events.urls")),
    path("analytics/", include("analytics.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Register custom error views
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
