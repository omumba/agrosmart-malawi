"""SMS Bot – URL Configuration"""

from django.urls import path
from . import views

app_name = 'sms_bot'

urlpatterns = [
    # Africa's Talking webhook
    path('incoming/',        views.sms_incoming,    name='sms_incoming'),

    # Admin / monitoring
    path('farmers/',         views.farmer_list,     name='farmer_list'),
    path('logs/',            views.sms_log_list,    name='sms_log_list'),
    path('broadcast/',       views.send_broadcast,  name='send_broadcast'),
    path('stats/',           views.platform_stats,  name='platform_stats'),
]
