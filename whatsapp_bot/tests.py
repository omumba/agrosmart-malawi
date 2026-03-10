"""
AgroSmart Malawi – WhatsApp Bot Tests
Run: python manage.py test whatsapp_bot.tests
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from sms_bot.models import FarmerProfile, SMSSession, SMSLog
from crops.models import Crop, Disease
from .whatsapp import WhatsAppProcessor, WhatsAppGateway


def make_crop_data():
    crop = Crop.objects.create(
        name_en='Maize', name_ny='Chimanga', slug='maize', icon='🌽', is_active=True
    )
    d1 = Disease.objects.create(
        crop=crop, menu_number=1,
        name_en='Maize Streak Virus', name_ny='Maize Streak',
        category='viral', severity='high',
        symptoms_en='Yellow streaks on leaves.',
        symptoms_ny='Mitsempha yakufiira.',
        treatment_en='Remove infected plants.\nApply insecticide.',
        treatment_ny='Chotsani mbewu.\nGwiritsani ntchito mankhwala.',
        recommended_product='Imidacloprid 200SL',
        is_active=True,
    )
    d2 = Disease.objects.create(
        crop=crop, menu_number=2,
        name_en='Northern Leaf Blight', name_ny='Northern Leaf Blight',
        category='fungal', severity='medium',
        symptoms_en='Cigar-shaped lesions.',
        symptoms_ny='Kuzizira kwa masamba.',
        treatment_en='Apply fungicide.',
        treatment_ny='Gwiritsani ntchito mankhwala a bowa.',
        recommended_product='Mancozeb',
        is_active=True,
    )
    return crop, d1, d2


class TestWhatsAppHelp(TestCase):
    def test_help_english(self):
        p = WhatsAppProcessor(phone='whatsapp:+265888000001', body='HELP')
        reply = p.process()
        self.assertIn('Welcome', reply)
        self.assertIn('MAIZE', reply)

    def test_help_chichewa(self):
        farmer = FarmerProfile.objects.create(phone_number='+265888000002', language='ny')
        p = WhatsAppProcessor(phone='whatsapp:+265888000002', body='HELP')
        reply = p.process()
        self.assertIn('Takulandirani', reply)
        self.assertIn('CHIMANGA', reply)

    def test_empty_body_shows_help(self):
        p = WhatsAppProcessor(phone='whatsapp:+265888000003', body='')
        reply = p.process()
        self.assertIn('Welcome', reply)

    def test_hello_shows_help(self):
        p = WhatsAppProcessor(phone='whatsapp:+265888000004', body='hello')
        reply = p.process()
        self.assertIn('Welcome', reply)


class TestWhatsAppCropQuery(TestCase):
    def setUp(self):
        self.crop, self.d1, self.d2 = make_crop_data()

    def test_maize_shows_disease_menu(self):
        p = WhatsAppProcessor(phone='whatsapp:+265888000010', body='MAIZE')
        reply = p.process()
        self.assertIn('Maize', reply)
        self.assertIn('Maize Streak Virus', reply)
        self.assertIn('Northern Leaf Blight', reply)

    def test_chimanga_chichewa(self):
        farmer = FarmerProfile.objects.create(phone_number='+265888000011', language='ny')
        p = WhatsAppProcessor(phone='whatsapp:+265888000011', body='CHIMANGA')
        reply = p.process()
        self.assertIn('Chimanga', reply)

    def test_menu_reply_returns_treatment(self):
        # First send MAIZE to open session
        p1 = WhatsAppProcessor(phone='whatsapp:+265888000012', body='MAIZE')
        p1.process()
        # Then reply with 1
        p2 = WhatsAppProcessor(phone='whatsapp:+265888000012', body='1')
        reply = p2.process()
        self.assertIn('Maize Streak Virus', reply)
        self.assertIn('Treatment', reply)

    def test_menu_reply_2_returns_second_disease(self):
        p1 = WhatsAppProcessor(phone='whatsapp:+265888000013', body='MAIZE')
        p1.process()
        p2 = WhatsAppProcessor(phone='whatsapp:+265888000013', body='2')
        reply = p2.process()
        self.assertIn('Northern Leaf Blight', reply)

    def test_invalid_menu_number_graceful(self):
        p1 = WhatsAppProcessor(phone='whatsapp:+265888000014', body='MAIZE')
        p1.process()
        p2 = WhatsAppProcessor(phone='whatsapp:+265888000014', body='9')
        reply = p2.process()
        self.assertIn('Invalid', reply)

    def test_session_created_on_crop_query(self):
        p = WhatsAppProcessor(phone='whatsapp:+265888000015', body='MAIZE')
        p.process()
        farmer = FarmerProfile.objects.get(phone_number='+265888000015')
        session = SMSSession.objects.get(farmer=farmer, state='active')
        self.assertEqual(session.context, 'maize')

    def test_session_closed_after_menu_reply(self):
        p1 = WhatsAppProcessor(phone='whatsapp:+265888000016', body='MAIZE')
        p1.process()
        p2 = WhatsAppProcessor(phone='whatsapp:+265888000016', body='1')
        p2.process()
        farmer = FarmerProfile.objects.get(phone_number='+265888000016')
        active = SMSSession.objects.filter(farmer=farmer, state='active').exists()
        self.assertFalse(active)


class TestWhatsAppLanguageSwitch(TestCase):
    def test_switch_to_chichewa(self):
        p = WhatsAppProcessor(phone='whatsapp:+265888000020', body='CHICHEWA')
        reply = p.process()
        self.assertIn('Chichewa', reply)
        farmer = FarmerProfile.objects.get(phone_number='+265888000020')
        self.assertEqual(farmer.language, 'ny')

    def test_switch_to_english(self):
        farmer = FarmerProfile.objects.create(phone_number='+265888000021', language='ny')
        p = WhatsAppProcessor(phone='whatsapp:+265888000021', body='ENGLISH')
        reply = p.process()
        self.assertIn('English', reply)
        farmer.refresh_from_db()
        self.assertEqual(farmer.language, 'en')


class TestWhatsAppPhoto(TestCase):
    def test_photo_message_handled(self):
        p = WhatsAppProcessor(
            phone='whatsapp:+265888000030', body='',
            media_url='https://example.com/img.jpg',
            media_type='image/jpeg',
        )
        reply = p.process()
        self.assertIn('Photo received', reply)

    def test_photo_chichewa(self):
        farmer = FarmerProfile.objects.create(phone_number='+265888000031', language='ny')
        p = WhatsAppProcessor(
            phone='whatsapp:+265888000031', body='',
            media_url='https://example.com/img.jpg',
            media_type='image/jpeg',
        )
        reply = p.process()
        self.assertIn('Chithunzi', reply)


class TestWhatsAppUnknown(TestCase):
    def test_unknown_message(self):
        p = WhatsAppProcessor(phone='whatsapp:+265888000040', body='XYZABC123')
        reply = p.process()
        self.assertIn("didn't understand", reply)

    def test_unknown_chichewa(self):
        farmer = FarmerProfile.objects.create(phone_number='+265888000041', language='ny')
        p = WhatsAppProcessor(phone='whatsapp:+265888000041', body='XYZABC123')
        reply = p.process()
        self.assertIn('Sindikumvetsa', reply)


class TestWhatsAppLogging(TestCase):
    def setUp(self):
        make_crop_data()

    def test_message_logged(self):
        p = WhatsAppProcessor(phone='whatsapp:+265888000050', body='MAIZE')
        p.process()
        farmer = FarmerProfile.objects.get(phone_number='+265888000050')
        count = SMSLog.objects.filter(farmer=farmer).count()
        self.assertGreater(count, 0, "Expected at least one SMSLog entry")

    def test_query_count_incremented(self):
        p = WhatsAppProcessor(phone='whatsapp:+265888000051', body='MAIZE')
        p.process()
        farmer = FarmerProfile.objects.get(phone_number='+265888000051')
        self.assertGreater(farmer.total_queries, 0)


class TestWhatsAppGateway(TestCase):
    @patch('twilio.rest.Client')
    def test_send_calls_twilio(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        gw = WhatsAppGateway()
        result = gw.send('whatsapp:+265888000060', 'Test message')
        self.assertIsInstance(result, bool)

    def test_send_failure_returns_false(self):
        """When Twilio credentials are missing, send() returns False gracefully."""
        gw = WhatsAppGateway()
        result = gw.send('whatsapp:+265888000061', 'Test message')
        self.assertFalse(result)
