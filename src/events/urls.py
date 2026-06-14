from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('stream/', views.sse_events, name='sse_stream'),
]
