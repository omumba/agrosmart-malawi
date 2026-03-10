"""
Management command: python manage.py seed_crops
Seeds the database with real Malawian crop disease data.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from crops.models import Crop, Disease


CROP_DATA = [
    {
        "name_en": "Maize",
        "name_ny": "Chimanga",
        "icon": "🌽",
        "slug": "maize",
        "diseases": [
            {
                "menu_number": 1,
                "name_en": "Maize Streak Virus",
                "name_ny": "Matenda a Maize Streak",
                "category": "viral",
                "severity": "high",
                "symptoms_en": "Yellow streaks along leaf veins. Stunted growth. Pale green or yellow striping on leaves.",
                "symptoms_ny": "Mitsempha yakufiira pa masamba. Kukula kwake kumayima. Masamba amaoneka achikasu kapena ofuwa.",
                "treatment_en": "Remove infected plants immediately\nApply imidacloprid insecticide to control leafhoppers\nPlant resistant varieties (MH18, SC403)\nAvoid planting near infected fields",
                "treatment_ny": "Chotsani mbewu zomwe zakhudzidwa nthawi yomweyo\nGwiritsani ntchito mankhwala a imidacloprid kuzipirira njenjete\nBwarani mbewu zotetezedwa (MH18, SC403)\nSamuka kubala pafupi ndi minda yomwe yakhuzidwa",
                "recommended_product": "Imidacloprid 200SL or Confidor",
            },
            {
                "menu_number": 2,
                "name_en": "Northern Leaf Blight",
                "name_ny": "Matenda a Leaf Blight",
                "category": "fungal",
                "severity": "medium",
                "symptoms_en": "Long greyish-tan cigar-shaped lesions on leaves. Lesions start on lower leaves and move upward.",
                "symptoms_ny": "Vipumu vitalitali vamivi pa masamba. Vipumu vyayamba pansi ndikwera.",
                "treatment_en": "Apply fungicide (mancozeb or chlorothalonil)\nRemove and destroy infected plant material\nEnsure good field drainage\nPlant certified disease-free seed",
                "treatment_ny": "Gwiritsani ntchito mankhwala a fungicide (mancozeb kapena chlorothalonil)\nChotsani ndi kuwotchera zomera zomwe zakhudzidwa\nOnetsetsani kuti munda ukusesa bwino\nBwarani mbewu zotetezedwa",
                "recommended_product": "Dithane M-45 (Mancozeb 80% WP)",
            },
            {
                "menu_number": 3,
                "name_en": "Fall Armyworm",
                "name_ny": "Phangirira la Fall Armyworm",
                "category": "pest",
                "severity": "critical",
                "symptoms_en": "Irregular holes in leaves. Frass (caterpillar droppings) in leaf whorls. Caterpillars visible in the whorl or on leaves.",
                "symptoms_ny": "Mabowo osakhala oyenera pa masamba. Kunyenya kwa nkhono m'mabale a masamba. Zipangirira zimaoneka m'mabale.",
                "treatment_en": "Spray with recommended insecticide early morning\nUse emamectin benzoate or lambda-cyhalothrin\nApply wood ash or sand in leaf whorls\nMonitor fields regularly for egg masses",
                "treatment_ny": "Fumirani ndi mankhwala oyenera m'mawa kwambiri\nGwiritsani ntchito emamectin benzoate kapena lambda-cyhalothrin\nIkani phulusa la nkhuni kapena mchenga m'mabale\nOnani minda kawirikawiri kwa mazira",
                "recommended_product": "Coragen (Chlorantraniliprole) or Ampligo",
            },
        ],
    },
    {
        "name_en": "Tomato",
        "name_ny": "Nyanya",
        "icon": "🍅",
        "slug": "tomato",
        "diseases": [
            {
                "menu_number": 1,
                "name_en": "Early Blight",
                "name_ny": "Matenda a Early Blight",
                "category": "fungal",
                "severity": "medium",
                "symptoms_en": "Dark brown spots with concentric rings on older leaves. Yellow halo around spots. Infected leaves drop early.",
                "symptoms_ny": "Maphwa akuda atonthorera pa masamba akale. Khalidwe loyera ozungulira maphwa. Masamba oyipa akugwa mofulumira.",
                "treatment_en": "Apply copper-based fungicide every 7-10 days\nRemove and destroy infected leaves\nAvoid overhead watering\nEnsure good air circulation between plants",
                "treatment_ny": "Fumirani ndi mankhwala a copper fungicide tsiku liri lonse 7-10\nChotsani ndi kuwotchera masamba oyipa\nSungani kusiyo kwa madzi pamwamba\nOnetsetsani mpweya wokwanira pakati pa zomera",
                "recommended_product": "Ridomil Gold MZ or Copper Oxychloride",
            },
            {
                "menu_number": 2,
                "name_en": "Tomato Leaf Curl Virus",
                "name_ny": "Matenda a Leaf Curl",
                "category": "viral",
                "severity": "high",
                "symptoms_en": "Leaves curl upward. Yellowing of leaf margins. Stunted plants. Fruit production drops severely.",
                "symptoms_ny": "Masamba amagwedeza kumwamba. Masamba amafuwa pa mphepete. Zomera zimayima. Zipatso zimachepera kwambiri.",
                "treatment_en": "Remove and destroy infected plants\nControl whitefly vectors with insecticide\nUse reflective mulch to deter whiteflies\nPlant resistant varieties where available",
                "treatment_ny": "Chotsani ndi kuwotchera mbewu zomwe zakhudzidwa\nPhani njenjete yoyera ndi mankhwala\nGwiritsani ntchito malichi oyakamula kuzindikira njenjete\nBwarani mbewu zotetezedwa",
                "recommended_product": "Actara (Thiamethoxam) for whitefly control",
            },
            {
                "menu_number": 3,
                "name_en": "Bacterial Wilt",
                "name_ny": "Matenda a Bacterial Wilt",
                "category": "bacterial",
                "severity": "high",
                "symptoms_en": "Sudden wilting of the whole plant. Leaves remain green initially. Brown discoloration inside stem. White bacterial ooze from cut stem.",
                "symptoms_ny": "Kufota kwamwayi kwa mbewu yonse. Masamba amasala azibiriti pachiyambi. Khungu lakuda mkati mwa msonga. Madzi achikasu achilala kuchoka ku msonga wodyedwa.",
                "treatment_en": "Remove and destroy infected plants immediately\nDo NOT compost infected material\nRotate crops - avoid tomato/potato on same land for 3 years\nImprove soil drainage\nUse certified disease-free transplants",
                "treatment_ny": "Chotsani ndi kuwotchera mbewu zomwe zakhudzidwa nthawi yomweyo\nMusagwiritse ntchito zomera zomwe zakhudzidwa ku kompositi\nSinthanitshani mbewu - musabale nyanya/mbatata pa malo omwe kwa zaka 3\nLaritsani kususetsa kwa munda\nGwiritsani ntchito nsembe zotetezedwa",
                "recommended_product": "No chemical cure. Prevention only.",
            },
        ],
    },
    {
        "name_en": "Cassava",
        "name_ny": "Chinangwa",
        "icon": "🥔",
        "slug": "cassava",
        "diseases": [
            {
                "menu_number": 1,
                "name_en": "Cassava Mosaic Disease",
                "name_ny": "Matenda a Cassava Mosaic",
                "category": "viral",
                "severity": "high",
                "symptoms_en": "Mosaic pattern of yellow-green on leaves. Distorted and twisted leaves. Stunted plant growth. Reduced tuber size.",
                "symptoms_ny": "Zojambula za achikasu-azibiriti pa masamba. Masamba osapinda ndi owemba. Kukula kwake kumayima. Zipatso zimafupika.",
                "treatment_en": "Use disease-free planting material (certified stems)\nRemove heavily infected plants\nControl whitefly vectors\nPlant tolerant varieties (TMS 30572, NASE 14)",
                "treatment_ny": "Gwiritsani ntchito zofera zomwe sizikhudza matenda (misonga yotetezedwa)\nChotsani mbewu zomwe zakhudzidwa kwambiri\nPhani njenjete yoyera\nBwarani mbewu zotetezedwa (TMS 30572, NASE 14)",
                "recommended_product": "Confidor (Imidacloprid) for whitefly; use clean planting material",
            },
            {
                "menu_number": 2,
                "name_en": "Cassava Brown Streak Disease",
                "name_ny": "Matenda a Brown Streak",
                "category": "viral",
                "severity": "critical",
                "symptoms_en": "Yellow or brown streaks on leaves. Brown corky patches inside roots/tubers. Severe yield loss possible.",
                "symptoms_ny": "Mitsempha yakufiira kapena yachikasu pa masamba. Maphwa akuda mkati mwa mizizi. Kutayika kwa zipatso kwambiri.",
                "treatment_en": "Use certified virus-tested planting material ONLY\nRogue out infected plants from the field\nControl whitefly with insecticide\nPlant resistant varieties (NASE 19, Narocas 1)",
                "treatment_ny": "Gwiritsani ntchito zofera zoyezedwa zachivirusi ZOKHA\nChotsani mbewu zomwe zakhudzidwa m'munda\nPhani njenjete yoyera ndi mankhwala\nBwarani mbewu zotetezedwa (NASE 19, Narocas 1)",
                "recommended_product": "Prevention only. Use clean planting material.",
            },
        ],
    },
    {
        "name_en": "Groundnut",
        "name_ny": "Nzama",
        "icon": "🥜",
        "slug": "groundnut",
        "diseases": [
            {
                "menu_number": 1,
                "name_en": "Groundnut Rosette Disease",
                "name_ny": "Matenda a Rosette",
                "category": "viral",
                "severity": "high",
                "symptoms_en": "Stunted plants with small, crinkled, mosaic leaves. Plants form compact rosette. Severely reduced pod set.",
                "symptoms_ny": "Zomera zimayima ndi masamba ang'ono owukuta, a mozaik. Zomera zimapanga rosette yolumikizana. Zipatso zimachepera kwambiri.",
                "treatment_en": "Plant early to avoid peak aphid season\nApply insecticide to control aphids\nRemove and destroy infected plants\nPlant resistant varieties (Chalimbana, CG7)",
                "treatment_ny": "Balani mofulumira kukana nthawi ya njenjete ya tirigu\nGwiritsani ntchito mankhwala kupha njenjete ya tirigu\nChotsani ndi kuwotchera mbewu zomwe zakhudzidwa\nBwarani mbewu zotetezedwa (Chalimbana, CG7)",
                "recommended_product": "Dimethoate or Chlorpyrifos for aphid control",
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the database with Malawian crop disease knowledge base"

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            Disease.objects.all().delete()
            Crop.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing crop/disease data."))

        total_crops    = 0
        total_diseases = 0

        for crop_data in CROP_DATA:
            diseases = crop_data.pop('diseases')

            crop, created = Crop.objects.update_or_create(
                slug=crop_data['slug'],
                defaults=crop_data,
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} crop: {crop.icon} {crop.name_en}")
            total_crops += 1

            for d in diseases:
                disease, dcreated = Disease.objects.update_or_create(
                    crop=crop,
                    menu_number=d['menu_number'],
                    defaults=d,
                )
                daction = "  ✓ Created" if dcreated else "  ↻ Updated"
                self.stdout.write(f"      {daction} disease: {disease.name_en}")
                total_diseases += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Seeded {total_crops} crops and {total_diseases} diseases successfully."
        ))
