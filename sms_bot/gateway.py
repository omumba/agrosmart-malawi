"""
SMS Gateway Service – Africa's Talking Integration
Handles sending SMS via Africa's Talking API.
Also supports broadcast messages to multiple farmers.
"""

import logging
import africastalking
from django.conf import settings
from celery import shared_task
from .models import FarmerProfile, SMSLog

logger = logging.getLogger(__name__)


def _init_at():
    """Initialise Africa's Talking SDK (lazy, once per request)."""
    africastalking.initialize(
        username=settings.AFRICAS_TALKING_USERNAME,
        api_key=settings.AFRICAS_TALKING_API_KEY,
    )
    return africastalking.SMS


class SMSGateway:
    """
    Wrapper around Africa's Talking SMS API.
    Provides send_sms() and broadcast() methods.
    """

    def __init__(self):
        self.sms = _init_at()
        self.sender = settings.AFRICAS_TALKING_SHORTCODE

    def send_sms(self, phone_number: str, message: str) -> dict:
        """
        Send a single SMS to one recipient.
        Returns the AT API response dict.
        """
        # Ensure E.164 format for Malawi (+265...)
        phone = self._normalise_number(phone_number)

        try:
            response = self.sms.send(
                message=message,
                recipients=[phone],
                sender_id=self.sender,
            )
            status = 'sent'
            at_id  = (
                response.get('SMSMessageData', {})
                        .get('Recipients', [{}])[0]
                        .get('messageId', '')
            )
            logger.info("SMS sent to %s | at_id=%s", phone, at_id)

        except Exception as exc:
            logger.error("SMS send failed to %s: %s", phone, exc)
            response = {}
            status   = 'failed'
            at_id    = ''

        # Log outbound
        SMSLog.objects.create(
            direction    = 'outbound',
            phone_number = phone_number,
            message      = message,
            status       = status,
            at_message_id = at_id,
        )

        return response

    def broadcast(self, phone_numbers: list[str], message: str) -> dict:
        """
        Send the same SMS to a list of phone numbers.
        Africa's Talking supports up to 1000 recipients per call.
        """
        normalised = [self._normalise_number(p) for p in phone_numbers]
        chunks = [normalised[i:i+1000] for i in range(0, len(normalised), 1000)]

        results = []
        for chunk in chunks:
            try:
                resp = self.sms.send(
                    message=message,
                    recipients=chunk,
                    sender_id=self.sender,
                )
                results.append(resp)
                logger.info("Broadcast sent to %d recipients", len(chunk))
            except Exception as exc:
                logger.error("Broadcast chunk failed: %s", exc)
                results.append({'error': str(exc)})

        return {'chunks': results, 'total_recipients': len(normalised)}

    @staticmethod
    def _normalise_number(phone: str) -> str:
        """Convert Malawian number to E.164 (+265...)."""
        phone = phone.strip().replace(' ', '').replace('-', '')
        if phone.startswith('0'):
            return '+265' + phone[1:]
        if phone.startswith('265') and not phone.startswith('+'):
            return '+' + phone
        return phone


# ── CELERY TASKS ─────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_task(self, phone_number: str, message: str):
    """
    Celery task to send a single SMS asynchronously.
    Retries up to 3 times on failure.
    """
    try:
        gateway = SMSGateway()
        return gateway.send_sms(phone_number, message)
    except Exception as exc:
        logger.error("send_sms_task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task
def broadcast_weather_alert_task(district: str, message: str):
    """
    Broadcast a weather alert to all active farmers in a district.
    Called by the weather service when severe weather is forecast.
    """
    farmers = FarmerProfile.objects.filter(
        district__iexact=district,
        is_active=True,
    ).values_list('phone_number', flat=True)

    if not farmers:
        logger.warning("No active farmers found in district: %s", district)
        return {'sent': 0}

    gateway = SMSGateway()
    result  = gateway.broadcast(list(farmers), message)
    logger.info("Weather alert broadcast: district=%s sent=%d", district, len(farmers))
    return result


@shared_task
def broadcast_market_prices_task(message: str):
    """
    Broadcast weekly market prices to all active farmers.
    """
    phones = list(
        FarmerProfile.objects.filter(is_active=True).values_list('phone_number', flat=True)
    )
    if not phones:
        return {'sent': 0}

    gateway = SMSGateway()
    return gateway.broadcast(phones, message)
