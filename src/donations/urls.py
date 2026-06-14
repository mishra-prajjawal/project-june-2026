from django.urls import path
from . import views

app_name = 'donations'

urlpatterns = [
    path('donor/', views.donor_dashboard, name='donor_dashboard'),
    path('ngo/', views.ngo_dashboard, name='ngo_dashboard'),
]
