from django.urls import path
from . import views

urlpatterns = [
    path('incoming/', views.whatsapp_incoming, name='whatsapp_incoming'),
    path('broadcast/', views.whatsapp_broadcast, name='whatsapp_broadcast'),
]
