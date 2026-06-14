from django.urls import path
from . import views

app_name = 'donations'

urlpatterns = [
    path('donor/', views.donor_dashboard, name='donor_dashboard'),
    path('ngo/', views.ngo_dashboard, name='ngo_dashboard'),
    path('post/', views.post_donation, name='post_donation'),
    path('claim/<int:donation_id>/', views.claim_donation_view, name='claim_donation'),
    path('collect/<int:donation_id>/', views.collect_donation_view, name='collect_donation'),
    path('feedback/<int:donation_id>/', views.submit_feedback_view, name='submit_feedback'),
]
