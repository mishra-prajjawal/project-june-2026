from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('report/', views.impact_report, name='report'),
]
