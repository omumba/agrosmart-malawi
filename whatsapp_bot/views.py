import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .whatsapp import WhatsAppProcessor, WhatsAppGateway
from sms_bot.models import FarmerProfile

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def whatsapp_incoming(request):
    """
    Twilio WhatsApp webhook.
    Twilio sends POST with: From, Body, MediaUrl0, MediaContentType0
    """
    try:
        phone      = request.data.get('From', '').strip()
        body       = request.data.get('Body', '').strip()
        media_url  = request.data.get('MediaUrl0', '').strip() or None
        media_type = request.data.get('MediaContentType0', '').strip() or None

        if not phone:
            return HttpResponse('Missing From', status=400)

        processor = WhatsAppProcessor(phone=phone, body=body,
                                      media_url=media_url, media_type=media_type)
        reply = processor.process()

        # Return TwiML response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message><Body>{reply}</Body></Message>
</Response>"""
        return HttpResponse(twiml, content_type='text/xml')

    except Exception as exc:
        logger.exception("WhatsApp webhook error: %s", exc)
        return HttpResponse('Error', status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def whatsapp_broadcast(request):
    """
    Admin endpoint: broadcast a WhatsApp message to all active farmers.
    POST body: { message, district (optional), language (optional) }
    """
    message  = request.data.get('message', '').strip()
    district = request.data.get('district', '').strip() or None
    language = request.data.get('language', '').strip() or None

    if not message:
        return Response({'error': 'message is required'}, status=status.HTTP_400_BAD_REQUEST)

    farmers = FarmerProfile.objects.filter(is_active=True)
    if district:
        farmers = farmers.filter(district__iexact=district)
    if language:
        farmers = farmers.filter(language=language)

    gateway = WhatsAppGateway()
    sent = 0
    errors = 0

    for farmer in farmers:
        wa_phone = f"whatsapp:{farmer.phone_number}"
        success = gateway.send(wa_phone, message)
        if success:
            sent += 1
        else:
            errors += 1

    return Response({
        'sent':   sent,
        'errors': errors,
        'total':  sent + errors,
    })
