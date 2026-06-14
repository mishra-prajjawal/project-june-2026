from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify/<int:user_id>/', views.verify_ngo, name='verify_ngo'),
    path('reject/<int:user_id>/', views.reject_ngo, name='reject_ngo'),
    path('toggle-ban/<int:user_id>/', views.toggle_ban, name='toggle_ban'),
]
