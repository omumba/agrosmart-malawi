"""
SMS Bot – Tests
Run: python manage.py test sms_bot
"""

import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from sms_bot.parser import SMSProcessor, CROP_KEYWORDS, INTENT_KEYWORDS
from sms_bot.models import FarmerProfile, SMSSession, SMSLog
from crops.models import Crop, Disease


# ── FIXTURES ─────────────────────────────────────────────────────────────────

def make_crop(name='Maize', slug='maize', icon='🌽'):
    return Crop.objects.create(
        name_en=name, name_ny='Chimanga', slug=slug, icon=icon, is_active=True
    )

def make_disease(crop, num=1):
    return Disease.objects.create(
        crop=crop,
        menu_number=num,
        name_en='Maize Streak Virus',
        name_ny='Matenda a Maize Streak',
        category='viral',
        severity='high',
        symptoms_en='Yellow streaks on leaves.',
        treatment_en='Remove infected plants.\nApply insecticide.',
        treatment_ny='Chotsani mbewu zomwe zakhudzidwa.',
        is_active=True,
    )


# ── FARMER PROFILE TESTS ─────────────────────────────────────────────────────

class TestFarmerProfile(TestCase):

    def test_farmer_created_on_first_sms(self):
        crop = make_crop()
        processor = SMSProcessor(phone_number='+265999123456', message='HELP')
        self.assertTrue(FarmerProfile.objects.filter(phone_number='+265999123456').exists())

    def test_farmer_language_defaults_to_english(self):
        processor = SMSProcessor(phone_number='+265999000001', message='HI')
        farmer = FarmerProfile.objects.get(phone_number='+265999000001')
        self.assertEqual(farmer.language, 'en')

    def test_query_count_increments(self):
        processor = SMSProcessor(phone_number='+265999000002', message='HELP')
        processor.process()
        farmer = FarmerProfile.objects.get(phone_number='+265999000002')
        self.assertEqual(farmer.total_queries, 1)


# ── INTENT DETECTION TESTS ────────────────────────────────────────────────────

class TestIntentDetection(TestCase):

    def _processor(self, msg, phone='+265999999999'):
        return SMSProcessor(phone_number=phone, message=msg)

    def test_greeting_intent(self):
        p = self._processor('HELLO')
        self.assertEqual(p._detect_intent(), 'greeting')

    def test_chichewa_greeting(self):
        p = self._processor('MONI')
        self.assertEqual(p._detect_intent(), 'greeting')

    def test_help_intent(self):
        p = self._processor('HELP')
        self.assertEqual(p._detect_intent(), 'help')

    def test_chichewa_help(self):
        p = self._processor('THANDIZO')
        self.assertEqual(p._detect_intent(), 'help')

    def test_crop_intent_maize(self):
        p = self._processor('MAIZE')
        self.assertEqual(p._detect_intent(), 'crop_query')

    def test_crop_intent_chichewa_maize(self):
        p = self._processor('CHIMANGA')
        self.assertEqual(p._detect_intent(), 'crop_query')

    def test_crop_intent_tomato(self):
        p = self._processor('TOMATO')
        self.assertEqual(p._detect_intent(), 'crop_query')

    def test_numeric_reply_intent(self):
        p = self._processor('1')
        self.assertEqual(p._detect_intent(), 'menu_reply')

    def test_weather_intent(self):
        p = self._processor('WEATHER LILONGWE')
        self.assertEqual(p._detect_intent(), 'weather')

    def test_market_intent(self):
        p = self._processor('PRICE MAIZE')
        self.assertEqual(p._detect_intent(), 'market')

    def test_language_switch_chichewa(self):
        p = self._processor('CHICHEWA')
        self.assertEqual(p._detect_intent(), 'language_ny')

    def test_language_switch_english(self):
        p = self._processor('ENGLISH')
        self.assertEqual(p._detect_intent(), 'language_en')

    def test_unknown_intent(self):
        p = self._processor('XYZZYX GIBBERISH 123')
        self.assertEqual(p._detect_intent(), 'unknown')


# ── RESPONSE TESTS ────────────────────────────────────────────────────────────

class TestSMSResponses(TestCase):

    def setUp(self):
        self.crop    = make_crop()
        self.disease = make_disease(self.crop)
        self.phone   = '+265888001001'

    def _process(self, msg, phone=None):
        p = SMSProcessor(phone_number=phone or self.phone, message=msg)
        return p.process()

    def test_greeting_response_contains_welcome(self):
        resp = self._process('HELLO', phone='+265888001002')
        self.assertIn('AgroSmart', resp)

    def test_help_response_contains_commands(self):
        resp = self._process('HELP', phone='+265888001003')
        self.assertIn('MAIZE', resp)

    def test_crop_query_shows_numbered_menu(self):
        resp = self._process('MAIZE', phone='+265888001004')
        self.assertIn('1.', resp)
        self.assertIn('Maize Streak Virus', resp)

    def test_crop_query_shows_reply_instruction(self):
        resp = self._process('MAIZE', phone='+265888001005')
        self.assertIn('Reply', resp.lower() if False else resp)

    def test_menu_reply_returns_treatment(self):
        phone = '+265888001006'
        # First: select crop
        self._process('MAIZE', phone=phone)
        # Then: select disease
        resp = self._process('1', phone=phone)
        self.assertIn('Remove infected plants', resp)

    def test_menu_reply_without_session_returns_expired(self):
        phone = '+265888001007'
        # Send a number without selecting a crop first
        resp = self._process('1', phone=phone)
        self.assertIn('session', resp.lower())

    def test_chichewa_language_switch(self):
        phone = '+265888001008'
        resp = self._process('CHICHEWA', phone=phone)
        self.assertIn('Chichewa', resp)
        farmer = FarmerProfile.objects.get(phone_number=phone)
        self.assertEqual(farmer.language, 'ny')

    def test_chichewa_crop_query_in_chichewa(self):
        phone = '+265888001009'
        self._process('CHICHEWA', phone=phone)
        resp = self._process('CHIMANGA', phone=phone)
        # Should return Chichewa crop name
        self.assertIn('Chimanga', resp)

    def test_unknown_command_returns_help_hint(self):
        resp = self._process('XYZABC123', phone='+265888001010')
        self.assertIn('HELP', resp)

    def test_weather_response_contains_weather(self):
        resp = self._process('WEATHER LILONGWE', phone='+265888001011')
        self.assertIn('Weather', resp)
        self.assertIn('Lilongwe', resp)

    def test_market_response_contains_prices(self):
        resp = self._process('PRICE MAIZE', phone='+265888001012')
        self.assertIn('MWK', resp)


# ── SMS LOG TESTS ─────────────────────────────────────────────────────────────

class TestSMSLogging(TestCase):

    def test_sms_is_logged_after_processing(self):
        processor = SMSProcessor(phone_number='+265777001001', message='HELP')
        processor.process()
        log = SMSLog.objects.filter(phone_number='+265777001001').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.intent, 'help')
        self.assertEqual(log.direction, 'inbound')

    def test_log_captures_intent(self):
        processor = SMSProcessor(phone_number='+265777001002', message='MAIZE')
        processor.process()
        log = SMSLog.objects.filter(phone_number='+265777001002').first()
        self.assertEqual(log.intent, 'crop_query')


# ── DISEASE FORMAT TEST ───────────────────────────────────────────────────────

class TestDiseaseFormat(TestCase):

    def setUp(self):
        self.crop    = make_crop()
        self.disease = make_disease(self.crop)

    def test_format_sms_response_english(self):
        resp = self.disease.format_sms_response(lang='en')
        self.assertIn('Maize Streak Virus', resp)
        self.assertIn('Remove infected plants', resp)

    def test_format_sms_response_chichewa(self):
        resp = self.disease.format_sms_response(lang='ny')
        self.assertIn('Chotsani', resp)
