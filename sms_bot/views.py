"""
SMS Bot – Views
Africa's Talking posts inbound SMS to /api/sms/incoming/
"""

import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .parser import SMSProcessor
from .gateway import SMSGateway, send_sms_task
from .models import FarmerProfile, SMSLog
from .serializers import FarmerProfileSerializer, SMSLogSerializer

logger = logging.getLogger(__name__)


# ── WEBHOOK (Africa's Talking) ────────────────────────────────────────────────

@csrf_exempt
@require_POST
def sms_incoming(request):
    """
    Africa's Talking webhook — receives inbound SMS from farmers.

    AT sends a POST with fields:
      from    – farmer's phone number
      text    – SMS body
      to      – shortcode
      date    – timestamp
      id      – AT message ID
    """
    phone   = request.POST.get('from', '').strip()
    message = request.POST.get('text', '').strip()
    at_id   = request.POST.get('id', '')

    if not phone or not message:
        logger.warning("SMS webhook: missing phone or message")
        return HttpResponse(status=400)

    logger.info("Inbound SMS | phone=%s | msg=%s | at_id=%s", phone, message[:60], at_id)

    try:
        processor = SMSProcessor(phone_number=phone, message=message)
        reply     = processor.process()

        # Send reply asynchronously via Celery
        send_sms_task.delay(phone, reply)

    except Exception as exc:
        logger.exception("Error processing SMS from %s: %s", phone, exc)
        # Always return 200 to AT so it doesn't retry endlessly
        fallback = "Sorry, a system error occurred. Please try again later."
        send_sms_task.delay(phone, fallback)

    # AT expects a 200 OK (body ignored)
    return HttpResponse("OK", status=200)


# ── ADMIN / MONITORING ENDPOINTS ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def farmer_list(request):
    """List all farmer profiles with pagination."""
    farmers = FarmerProfile.objects.all().order_by('-last_contact')
    serializer = FarmerProfileSerializer(farmers, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def sms_log_list(request):
    """
    Recent SMS log for admin monitoring.
    Optional query params: ?phone=+26599...  ?intent=crop_query
    """
    logs = SMSLog.objects.select_related('farmer').all()

    phone  = request.query_params.get('phone')
    intent = request.query_params.get('intent')

    if phone:
        logs = logs.filter(phone_number__contains=phone)
    if intent:
        logs = logs.filter(intent=intent)

    logs = logs[:100]
    serializer = SMSLogSerializer(logs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_broadcast(request):
    """
    Admin endpoint to send a manual broadcast SMS to all farmers.
    POST body: { "message": "..." }
    """
    message = request.data.get('message', '').strip()
    if not message:
        return Response({'error': 'message is required'}, status=status.HTTP_400_BAD_REQUEST)
    if len(message) > 160:
        return Response({'error': 'Message exceeds 160 characters'}, status=status.HTTP_400_BAD_REQUEST)

    phones = list(
        FarmerProfile.objects.filter(is_active=True).values_list('phone_number', flat=True)
    )
    if not phones:
        return Response({'sent': 0, 'message': 'No active farmers found'})

    gateway = SMSGateway()
    result  = gateway.broadcast(phones, message)
    return Response({'sent': len(phones), 'result': result})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def platform_stats(request):
    """Quick stats for admin dashboard overview card."""
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    stats = {
        'total_farmers':    FarmerProfile.objects.count(),
        'active_today':     FarmerProfile.objects.filter(last_contact__date=today).count(),
        'active_this_week': FarmerProfile.objects.filter(last_contact__date__gte=week_ago).count(),
        'total_sms':        SMSLog.objects.count(),
        'sms_today':        SMSLog.objects.filter(created_at__date=today).count(),
        'top_intents':      list(
            SMSLog.objects
            .values('intent')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        ),
        'language_breakdown': {
            'english':  FarmerProfile.objects.filter(language='en').count(),
            'chichewa': FarmerProfile.objects.filter(language='ny').count(),
        }
    }
    return Response(stats)
