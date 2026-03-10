"""
AgroSmart Malawi – WhatsApp Bot Processor
Handles incoming WhatsApp messages via Twilio.
Richer formatting than SMS: bold (*text*), emojis, multi-line.
"""

import logging
from django.conf import settings
from sms_bot.models import FarmerProfile, SMSSession, SMSLog
from crops.models import Crop, Disease

logger = logging.getLogger(__name__)


class WhatsAppGateway:
    """Sends WhatsApp messages via Twilio."""

    def send(self, to_phone: str, message: str) -> bool:
        try:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                from_=settings.TWILIO_WHATSAPP_FROM,
                to=to_phone,
                body=message,
            )
            logger.info("WhatsApp sent to %s", to_phone)
            return True
        except Exception as exc:
            logger.warning("WhatsApp send failed to %s: %s", to_phone, exc)
            return False


class WhatsAppProcessor:
    """
    Processes incoming WhatsApp messages.
    Shares session state with the SMS bot (same DB tables).
    Richer responses: bold, emojis, multi-line lists.
    """

    def __init__(self, phone: str, body: str, media_url: str = None, media_type: str = None):
        # Normalise phone — strip 'whatsapp:' prefix for DB storage
        self.raw_phone  = phone
        self.phone      = phone.replace('whatsapp:', '')
        self.body       = body or ''
        self.media_url  = media_url
        self.media_type = media_type
        self.cleaned    = self.body.strip().upper()

        # Load or create farmer profile
        self.farmer, _ = FarmerProfile.objects.get_or_create(
            phone_number=self.phone,
            defaults={'language': 'en'},
        )
        self.lang = self.farmer.language

        # Load active session
        self.session = SMSSession.objects.filter(
            farmer=self.farmer, state='active'
        ).first()

    def process(self) -> str:
        """Route message and return reply string."""

        # ── Photo received ────────────────────────────────────────────────────
        if self.media_url and self.media_type and 'image' in self.media_type:
            reply = self._handle_photo()

        # ── Language switch ───────────────────────────────────────────────────
        elif self.cleaned in ('CHICHEWA', 'NY', 'CHICHEWA/NY'):
            self.farmer.language = 'ny'
            self.farmer.save(update_fields=['language'])
            self.lang = 'ny'
            reply = (
                "🇲🇼 *Tasintha kulankhula Chichewa!*\n\n"
                "Lembani dzina la mbewu yanu:\n"
                "🌽 CHIMANGA  🍅 NYANYA  🥔 CHINANGWA\n"
                "🥜 NZAMA  🫘 NSEMBE  🫛 NYEMBA\n\n"
                "_Lembani HELP kuti muwone zonse._"
            )
        elif self.cleaned in ('ENGLISH', 'EN'):
            self.farmer.language = 'en'
            self.farmer.save(update_fields=['language'])
            self.lang = 'en'
            reply = (
                "🇬🇧 *Switched to English!*\n\n"
                "Type your crop name to get started:\n"
                "🌽 MAIZE  🍅 TOMATO  🥔 CASSAVA\n"
                "🥜 GROUNDNUT  🫘 SOYBEAN  🫛 BEANS\n\n"
                "_Type HELP to see all options._"
            )

        # ── Active session: numbered menu reply ───────────────────────────────
        elif self.session and self.cleaned.isdigit():
            reply = self._handle_menu_reply(int(self.cleaned))

        # ── Crop query ────────────────────────────────────────────────────────
        elif self._detect_crop():
            reply = self._handle_crop_query()

        # ── Weather ───────────────────────────────────────────────────────────
        elif 'WEATHER' in self.cleaned or 'NYENGO' in self.cleaned:
            reply = self._handle_weather()

        # ── Market prices ─────────────────────────────────────────────────────
        elif 'PRICE' in self.cleaned or 'MTENGO' in self.cleaned:
            reply = self._handle_market()

        # ── Help ──────────────────────────────────────────────────────────────
        elif self.cleaned in ('HELP', 'THANDIZO', 'HI', 'HELLO', 'START', ''):
            reply = self._handle_help()

        # ── Unknown ───────────────────────────────────────────────────────────
        else:
            reply = self._handle_unknown()

        # Log the interaction
        self._log(reply)
        self.farmer.increment_queries()
        return reply

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _handle_photo(self) -> str:
        """Photo received — AI diagnosis will be added in Stage 4."""
        if self.lang == 'ny':
            return (
                "📸 *Chithunzi chalandidwa!*\n\n"
                "🤖 Ntchito yathu ya AI ikukonzedwa kuti ithe kusanthula zithunzi.\n"
                "Pakadali pano, longosolani matenda pogwiritsa ntchito mawu:\n\n"
                "🌽 Lembani *CHIMANGA* ndikusankha chiwerengero\n"
                "🍅 Lembani *NYANYA* ndikusankha chiwerengero\n\n"
                "_Zinthu za AI zikubwera posachedwa!_"
            )
        return (
            "📸 *Photo received!*\n\n"
            "🤖 Our AI diagnosis feature is coming in the next update.\n"
            "For now, describe the disease using text:\n\n"
            "🌽 Type *MAIZE* and select from the menu\n"
            "🍅 Type *TOMATO* and select from the menu\n\n"
            "_Full AI photo diagnosis coming soon!_"
        )

    def _handle_help(self) -> str:
        if self.lang == 'ny':
            return (
                "🌱 *Takulandirani ku AgroSmart Malawi!*\n\n"
                "*Malamulo:*\n"
                "🌽 *CHIMANGA* — matenda a chimanga\n"
                "🍅 *NYANYA* — matenda a nyanya\n"
                "🥔 *CHINANGWA* — matenda a chinangwa\n"
                "🥜 *NZAMA* — matenda a nzama\n"
                "🌦️ *NYENGO* — nyengo ya lero\n"
                "💰 *MTENGO* — mitengo ya msika\n"
                "🇬🇧 *ENGLISH* — sinthani chilankhulo\n\n"
                "_Thandizo la ulimi wa Malawi · AgroSmart_"
            )
        return (
            "🌱 *Welcome to AgroSmart Malawi!*\n\n"
            "*Commands:*\n"
            "🌽 *MAIZE* — maize disease advice\n"
            "🍅 *TOMATO* — tomato disease advice\n"
            "🥔 *CASSAVA* — cassava disease advice\n"
            "🥜 *GROUNDNUT* — groundnut disease advice\n"
            "🌦️ *WEATHER* — today's farm weather\n"
            "💰 *PRICE* — market prices\n"
            "🇲🇼 *CHICHEWA* — switch to Chichewa\n\n"
            "_Serving 4M+ Malawian farmers · AgroSmart_"
        )

    def _handle_crop_query(self) -> str:
        """Show disease menu for a crop."""
        crop_slug = self._detect_crop()
        try:
            crop     = Crop.objects.get(slug=crop_slug)
            diseases = Disease.objects.filter(crop=crop).order_by('menu_number')

            if self.lang == 'ny':
                lines = [f"🌿 *{crop.name_ny} — Matenda:*\n"]
                for d in diseases:
                    lines.append(f"  *{d.menu_number}.* {d.name_ny}")
                lines.append(f"\n_Lembani nambala (mwachitsanzo: 1)_")
            else:
                lines = [f"🌿 *{crop.name_en} — Diseases:*\n"]
                for d in diseases:
                    lines.append(f"  *{d.menu_number}.* {d.name_en}")
                lines.append(f"\n_Reply with a number (e.g. 1) for treatment_")

            # Save session
            if self.session:
                self.session.context = crop_slug
                self.session.save(update_fields=['context', 'updated_at'])
            else:
                SMSSession.objects.create(
                    farmer=self.farmer,
                    context=crop_slug,
                    state='active',
                )

            return '\n'.join(lines)

        except Crop.DoesNotExist:
            return self._handle_unknown()

    def _handle_menu_reply(self, number: int) -> str:
        """Return treatment for selected disease number."""
        if not self.session or not self.session.context:
            return self._handle_help()

        try:
            crop    = Crop.objects.get(slug=self.session.context)
            disease = Disease.objects.get(crop=crop, menu_number=number)

            icon = {'fungal': '🍄', 'viral': '🦠', 'pest': '🐛', 'bacterial': '🔬'}.get(
                disease.category, '⚠️')

            if self.lang == 'ny':
                treatment_lines = '\n'.join(
                    f"✅ {l.strip()}" for l in disease.treatment_ny.split('\n') if l.strip()
                )
                reply = (
                    f"{icon} *{disease.name_ny}*\n\n"
                    f"*Matenda:*\n{disease.symptoms_ny[:200]}\n\n"
                    f"*Chithandizo:*\n{treatment_lines}\n\n"
                    f"*Chithandizo chodziwika:* {disease.recommended_product or 'Onani kuchipitala'}\n\n"
                    f"_Lembani dzina la mbewu ina kuti mupitirire._"
                )
            else:
                treatment_lines = '\n'.join(
                    f"✅ {l.strip()}" for l in disease.treatment_en.split('\n') if l.strip()
                )
                reply = (
                    f"{icon} *{disease.name_en}*\n\n"
                    f"*Symptoms:*\n{disease.symptoms_en[:200]}\n\n"
                    f"*Treatment:*\n{treatment_lines}\n\n"
                    f"*Recommended product:* {disease.recommended_product or 'Consult agro-dealer'}\n\n"
                    f"_Type another crop name to continue._"
                )

            # Close session
            self.session.state = 'expired'
            self.session.save(update_fields=['state'])
            return reply

        except Disease.DoesNotExist:
            return (
                f"❌ Invalid choice. Please reply with a number from the menu.\n"
                f"Type *{self.session.context.upper()}* to see the menu again."
            )

    def _handle_weather(self) -> str:
        words    = self.cleaned.split()
        district = words[1].lower() if len(words) > 1 else (self.farmer.district or 'lilongwe')
        if self.lang == 'ny':
            return (
                f"🌦️ *Nyengo – {district.title()}*\n\n"
                "Chidziwitso cha nyengo chikubwera posachedwa.\n"
                "_(OpenWeatherMap ikuphatikizidwa mu Stage 4)_\n\n"
                "_Lembani HELP kuti muwone zonse._"
            )
        return (
            f"🌦️ *Weather – {district.title()}*\n\n"
            "Live weather data coming soon.\n"
            "_(OpenWeatherMap integration in Stage 4)_\n\n"
            "_Type HELP to see all commands._"
        )

    def _handle_market(self) -> str:
        if self.lang == 'ny':
            return (
                "💰 *Mitengo ya Msika*\n\n"
                "🌽 Chimanga:   MWK 650/kg\n"
                "🥜 Nzama:     MWK 1,800/kg\n"
                "🫘 Nsembe:    MWK 1,200/kg\n"
                "🥔 Chinangwa: MWK 280/kg\n"
                "🫛 Nyemba:    MWK 1,100/kg\n\n"
                "_Mitengo yowerengeredwa. Imasiyana pa msika uliwonse._"
            )
        return (
            "💰 *Market Prices*\n\n"
            "🌽 Maize:     MWK 650/kg\n"
            "🥜 Groundnut: MWK 1,800/kg\n"
            "🫘 Soybean:   MWK 1,200/kg\n"
            "🥔 Cassava:   MWK 280/kg\n"
            "🫛 Beans:     MWK 1,100/kg\n\n"
            "_Estimated prices. Negotiate wisely._"
        )

    def _handle_unknown(self) -> str:
        if self.lang == 'ny':
            return (
                "❓ Sindikumvetsa uthenga wanu.\n\n"
                "Lembani *HELP* kuti muwone malamulo onse.\n"
                "Kapena lembani dzina la mbewu:\n"
                "*CHIMANGA · NYANYA · CHINANGWA · NZAMA*"
            )
        return (
            "❓ I didn't understand that.\n\n"
            "Type *HELP* to see all commands.\n"
            "Or type a crop name:\n"
            "*MAIZE · TOMATO · CASSAVA · GROUNDNUT*"
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _detect_crop(self):
        """Return crop slug if message matches a crop keyword."""
        crop_keywords = {
            'maize':     ['MAIZE', 'CORN', 'CHIMANGA'],
            'tomato':    ['TOMATO', 'NYANYA'],
            'cassava':   ['CASSAVA', 'CHINANGWA'],
            'groundnut': ['GROUNDNUT', 'PEANUT', 'NZAMA'],
            'soybean':   ['SOYBEAN', 'SOY', 'NSEMBE'],
            'beans':     ['BEANS', 'BEAN', 'NYEMBA'],
        }
        for slug, keywords in crop_keywords.items():
            if any(kw in self.cleaned for kw in keywords):
                return slug
        return None

    def _log(self, response: str):
        try:
            # Use only fields confirmed to exist on SMSLog
            sms_log_fields = {f.name for f in SMSLog._meta.local_fields}
            log_fields = {'farmer': self.farmer, 'message': self.body[:500]}
            if 'phone_number' in sms_log_fields:
                log_fields['phone_number'] = self.raw_phone
            if 'response' in sms_log_fields:
                log_fields['response'] = response[:500]
            if 'direction' in sms_log_fields:
                log_fields['direction'] = 'inbound'
            if 'status' in sms_log_fields:
                log_fields['status'] = 'processed'
            if 'channel' in sms_log_fields:
                log_fields['channel'] = 'whatsapp'
            SMSLog.objects.create(**log_fields)
        except Exception as exc:
            logger.warning("Failed to log WhatsApp message: %s", exc)
