"""Celery configuration for AgroSmart async tasks."""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrosmart.settings')

app = Celery('agrosmart')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
