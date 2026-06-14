from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
]
