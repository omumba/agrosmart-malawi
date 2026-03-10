"""
SMS Bot – Models
Tracks farmer sessions, message logs, and conversation state.
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class FarmerProfile(models.Model):
    """Minimal farmer record created on first SMS contact."""

    LANGUAGE_CHOICES = [('en', 'English'), ('ny', 'Chichewa')]

    phone_number  = models.CharField(max_length=20, unique=True, db_index=True)
    language      = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    district      = models.CharField(max_length=100, blank=True)
    first_contact = models.DateTimeField(auto_now_add=True)
    last_contact  = models.DateTimeField(auto_now=True)
    total_queries = models.PositiveIntegerField(default=0)
    is_active     = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Farmer Profile'
        ordering = ['-last_contact']

    def __str__(self):
        return f"{self.phone_number} ({self.get_language_display()})"

    def increment_queries(self):
        self.total_queries += 1
        self.save(update_fields=['total_queries', 'last_contact'])


class SMSSession(models.Model):
    """
    Tracks a farmer's conversation state so multi-step menus work.
    e.g. Farmer texts MAIZE → sees menu → texts 1 → gets disease detail.
    """

    STATE_CHOICES = [
        ('idle',           'Idle'),
        ('crop_selected',  'Crop Selected'),
        ('awaiting_menu',  'Awaiting Menu Choice'),
        ('language_select','Language Selection'),
    ]

    farmer      = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='sessions')
    state       = models.CharField(max_length=30, choices=STATE_CHOICES, default='idle')
    context     = models.JSONField(default=dict, help_text="Current conversation context")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        get_latest_by = 'updated_at'

    def __str__(self):
        return f"Session({self.farmer.phone_number}, {self.state})"

    @property
    def is_expired(self) -> bool:
        timeout = settings.SMS_BOT.get('SESSION_TIMEOUT_MINUTES', 30)
        return self.updated_at < timezone.now() - timedelta(minutes=timeout)

    def reset(self):
        self.state   = 'idle'
        self.context = {}
        self.save(update_fields=['state', 'context', 'updated_at'])

    def set_state(self, state: str, **context_kwargs):
        self.state = state
        self.context.update(context_kwargs)
        self.save(update_fields=['state', 'context', 'updated_at'])


class SMSLog(models.Model):
    """Full audit log of every inbound and outbound SMS."""

    DIRECTION_CHOICES = [('inbound', 'Inbound'), ('outbound', 'Outbound')]
    STATUS_CHOICES    = [
        ('received',  'Received'),
        ('processed', 'Processed'),
        ('sent',      'Sent'),
        ('failed',    'Failed'),
    ]

    farmer      = models.ForeignKey(FarmerProfile, on_delete=models.SET_NULL, null=True, related_name='logs')
    direction   = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    phone_number = models.CharField(max_length=20, db_index=True)
    message     = models.TextField()
    response    = models.TextField(blank=True)
    status      = models.CharField(max_length=15, choices=STATUS_CHOICES, default='received')
    intent      = models.CharField(max_length=100, blank=True, help_text="Detected intent, e.g. 'crop_disease'")
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    at_message_id = models.CharField(max_length=100, blank=True, help_text="Africa's Talking message ID")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'SMS Log'
        verbose_name_plural = 'SMS Logs'

    def __str__(self):
        return f"[{self.direction}] {self.phone_number}: {self.message[:50]}"
