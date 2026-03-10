"""
SMS Bot – Parser & Response Engine
The brain of the SMS advisory system.

Flow:
  1. Incoming SMS arrives at webhook
  2. Parser identifies intent from raw text
  3. Session manager handles multi-turn state
  4. Response builder formats the reply (≤160 chars per SMS)
  5. Africa's Talking gateway sends response
"""

import logging
from typing import Optional
from django.conf import settings
from crops.models import Crop, Disease
from .models import FarmerProfile, SMSSession, SMSLog

logger = logging.getLogger(__name__)


# ── INTENT KEYWORDS ──────────────────────────────────────────────────────────

# Maps raw SMS keywords to crop slugs
CROP_KEYWORDS = {
    # English
    'MAIZE':        'maize',
    'CHIMANGA':     'maize',   # Chichewa
    'CORN':         'maize',
    'TOMATO':       'tomato',
    'TOMATO':       'tomato',
    'NYANYA':       'tomato',  # Chichewa
    'CASSAVA':      'cassava',
    'CHINANGWA':    'cassava', # Chichewa
    'GROUNDNUT':    'groundnut',
    'NZAMA':        'groundnut',
    'SOYBEAN':      'soybean',
    'NSEMBE':       'soybean',
    'BEANS':        'beans',
    'NYEMBA':       'beans',
    'RICE':         'rice',
    'MPUNGA':       'rice',
}

# Maps keywords to handler names
INTENT_KEYWORDS = {
    # Weather
    'WEATHER':   'weather',
    'MVULA':     'weather',   # Chichewa: rain/weather
    'RAIN':      'weather',
    # Market prices
    'PRICE':     'market',
    'PRICES':    'market',
    'MTENGO':    'market',    # Chichewa: price
    'MARKET':    'market',
    # Language switch
    'CHICHEWA':  'language_ny',
    'ENGLISH':   'language_en',
    # Help
    'HELP':      'help',
    'INFO':      'help',
    'THANDIZO':  'help',      # Chichewa: help
    # Greeting
    'HI':        'greeting',
    'HELLO':     'greeting',
    'MONI':      'greeting',  # Chichewa: hello
}

# ── RESPONSE TEMPLATES ───────────────────────────────────────────────────────

RESPONSES = {
    'en': {
        'greeting': (
            "Welcome to AgroSmart Malawi! 🌱\n"
            "Your free farm advisory service.\n\n"
            "Type a crop name:\nMAIZE  TOMATO  CASSAVA\n"
            "GROUNDNUT  SOYBEAN  BEANS\n\n"
            "Or type HELP for all commands."
        ),
        'help': (
            "AgroSmart Commands:\n"
            "• MAIZE / TOMATO / CASSAVA\n"
            "• WEATHER [district]\n"
            "• PRICE [crop]\n"
            "• CHICHEWA - switch language\n"
            "Free service. Powered by AgroSmart."
        ),
        'language_changed': "Language set to English. ✓\nType HELP for commands.",
        'unknown': (
            "Sorry, I did not understand.\n"
            "Type HELP for available commands\n"
            "or a crop name like MAIZE."
        ),
        'crop_menu': "{icon} {crop} Diseases:\n{items}\n\nReply with a number for treatment advice.",
        'no_diseases': "No disease info available for {crop} yet. Type HELP for other options.",
        'session_expired': "Your session expired. Type a crop name to start again.",
    },
    'ny': {
        'greeting': (
            "Mwalandiridwa ku AgroSmart Malawi! 🌱\n"
            "Ntchito yanu yaulere ya ulangizi wa ulimi.\n\n"
            "Lembani dzina la mbewu:\nCHIMANGA  NYANYA  CHINANGWA\n"
            "NZAMA  NYEMBA\n\nLembani THANDIZO pazalamulo."
        ),
        'help': (
            "Malamulo a AgroSmart:\n"
            "• CHIMANGA / NYANYA / CHINANGWA\n"
            "• MVULA [dera]\n"
            "• MTENGO [mbewu]\n"
            "• ENGLISH - sinthani chinenero\n"
            "Ntchito yaulere."
        ),
        'language_changed': "Chinenero wasinthidwa ku Chichewa. ✓\nLembani THANDIZO.",
        'unknown': (
            "Pepani, sindinazmvetsetse.\n"
            "Lembani THANDIZO pazalamulo\n"
            "kapena dzina la mbewu monga CHIMANGA."
        ),
        'crop_menu': "{icon} Matenda a {crop}:\n{items}\n\nYankhanani ndi nambala kuti mulandire malangizo.",
        'no_diseases': "Palibe chidziwitso pa {crop} panopa. Lembani THANDIZO.",
        'session_expired': "Nthawi yanu idatha. Lembani dzina la mbewu kuti muyambenso.",
    },
}


# ── MAIN PROCESSOR ───────────────────────────────────────────────────────────

class SMSProcessor:
    """
    Processes an incoming SMS and returns a response string.
    Handles session state for multi-step menus.
    """

    def __init__(self, phone_number: str, message: str):
        self.phone_number = phone_number.strip()
        self.raw_message  = message.strip()
        self.cleaned      = message.strip().upper()
        self.farmer       = self._get_or_create_farmer()
        self.lang         = self.farmer.language
        self.session      = self._get_or_create_session()
        self.response     = ""
        self.intent       = "unknown"

    # ── Farmer / Session helpers ──────────────────────────────────────────────

    def _get_or_create_farmer(self) -> FarmerProfile:
        farmer, _ = FarmerProfile.objects.get_or_create(
            phone_number=self.phone_number,
            defaults={'language': settings.SMS_BOT.get('DEFAULT_LANGUAGE', 'en')}
        )
        return farmer

    def _get_or_create_session(self) -> SMSSession:
        session, created = SMSSession.objects.get_or_create(farmer=self.farmer)
        if not created and session.is_expired:
            session.reset()
        return session

    def t(self, key: str, **kwargs) -> str:
        """Translate a response template."""
        template = RESPONSES.get(self.lang, RESPONSES['en']).get(key, '')
        return template.format(**kwargs) if kwargs else template

    # ── Intent detection ──────────────────────────────────────────────────────

    def _detect_intent(self) -> str:
        """
        Determine intent from the cleaned message.
        Priority: numeric reply > crop keyword > intent keyword > unknown
        """
        # Numeric: farmer is responding to a menu
        if self.cleaned.isdigit():
            return 'menu_reply'

        # Check each word in the message
        words = self.cleaned.split()
        first_word = words[0] if words else ''

        if first_word in CROP_KEYWORDS:
            return 'crop_query'

        if first_word in INTENT_KEYWORDS:
            return INTENT_KEYWORDS[first_word]

        # Fallback: scan all words
        for word in words:
            if word in CROP_KEYWORDS:
                return 'crop_query'
            if word in INTENT_KEYWORDS:
                return INTENT_KEYWORDS[word]

        return 'unknown'

    # ── Intent handlers ───────────────────────────────────────────────────────

    def _handle_greeting(self) -> str:
        return self.t('greeting')

    def _handle_help(self) -> str:
        return self.t('help')

    def _handle_language_change(self, intent: str) -> str:
        new_lang = 'ny' if intent == 'language_ny' else 'en'
        self.farmer.language = new_lang
        self.farmer.save(update_fields=['language'])
        self.lang = new_lang
        self.session.reset()
        return self.t('language_changed')

    def _handle_crop_query(self) -> str:
        """Show the disease menu for a crop."""
        # Identify which crop
        crop_slug = None
        for word in self.cleaned.split():
            if word in CROP_KEYWORDS:
                crop_slug = CROP_KEYWORDS[word]
                break

        try:
            crop = Crop.objects.prefetch_related('diseases').get(slug=crop_slug, is_active=True)
        except Crop.DoesNotExist:
            return self.t('unknown')

        diseases = crop.diseases.filter(is_active=True).order_by('menu_number')[:5]

        if not diseases:
            return self.t('no_diseases', crop=crop.get_name(self.lang))

        # Build numbered list
        items = '\n'.join(
            f"{d.menu_number}. {d.get_name(self.lang)}"
            for d in diseases
        )

        # Save state so we know which crop the next numeric reply refers to
        self.session.set_state('awaiting_menu', crop_slug=crop_slug)

        return self.t(
            'crop_menu',
            icon=crop.icon,
            crop=crop.get_name(self.lang),
            items=items,
        )

    def _handle_menu_reply(self) -> str:
        """Farmer replied with a number — show full disease treatment."""
        if self.session.state != 'awaiting_menu':
            # Session lost context; treat as new query
            self.session.reset()
            return self.t('session_expired')

        crop_slug  = self.session.context.get('crop_slug')
        menu_num   = int(self.cleaned)

        try:
            crop    = Crop.objects.get(slug=crop_slug)
            disease = Disease.objects.get(crop=crop, menu_number=menu_num, is_active=True)
        except (Crop.DoesNotExist, Disease.DoesNotExist):
            self.session.reset()
            return self.t('unknown')

        self.session.reset()   # Back to idle after full answer
        return disease.format_sms_response(lang=self.lang)

    def _handle_weather(self) -> str:
        """Stub – replaced by live weather in Stage 4."""
        words = self.cleaned.split()
        district = words[1].title() if len(words) > 1 else "Lilongwe"
        return (
            f"🌦 Weather – {district}\n"
            "Live weather coming in Stage 4.\n"
            "Visit agrosmart.mw for forecasts."
        )

    def _handle_market(self) -> str:
        """Stub – replaced by live prices in Stage 4."""
        return (
            "📊 Market Prices (Demo)\n"
            "Maize:     MWK 650/kg\n"
            "Groundnut: MWK 1,800/kg\n"
            "Soybean:   MWK 1,200/kg\n"
            "Live prices coming in Stage 4."
        )

    def _handle_unknown(self) -> str:
        return self.t('unknown')

    # ── Main entry point ──────────────────────────────────────────────────────

    def process(self) -> str:
        """
        Main method: detect intent → dispatch → return response string.
        Also updates farmer query count and logs the exchange.
        """
        intent = self._detect_intent()
        self.intent = intent

        handler_map = {
            'greeting':     self._handle_greeting,
            'help':         self._handle_help,
            'crop_query':   self._handle_crop_query,
            'menu_reply':   self._handle_menu_reply,
            'weather':      self._handle_weather,
            'market':       self._handle_market,
            'language_ny':  lambda: self._handle_language_change('language_ny'),
            'language_en':  lambda: self._handle_language_change('language_en'),
            'unknown':      self._handle_unknown,
        }

        handler  = handler_map.get(intent, self._handle_unknown)
        response = handler()

        # Update farmer stats
        self.farmer.increment_queries()

        # Log the exchange
        SMSLog.objects.create(
            farmer       = self.farmer,
            direction    = 'inbound',
            phone_number = self.phone_number,
            message      = self.raw_message,
            response     = response,
            status       = 'processed',
            intent       = intent,
        )

        logger.info(
            "SMS processed | phone=%s | intent=%s | lang=%s",
            self.phone_number, intent, self.lang
        )

        return response
