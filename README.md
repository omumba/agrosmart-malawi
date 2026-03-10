# AgroSmart Malawi – Stage 2: SMS Advisory Bot Backend

AI-powered crop advisory platform for Malawian farmers.
Built with Python/Django + Africa's Talking SMS Gateway.

---

## 🗂 Project Structure

```
agrosmart/
├── agrosmart/          # Django project config
│   ├── settings.py     # All configuration
│   ├── urls.py         # Root URL routing
│   └── celery.py       # Async task queue
├── sms_bot/            # Core SMS bot engine
│   ├── parser.py       # Intent detection + response engine
│   ├── gateway.py      # Africa's Talking integration
│   ├── models.py       # FarmerProfile, SMSSession, SMSLog
│   ├── views.py        # Webhook + admin API endpoints
│   └── tests/          # Unit tests
├── crops/              # Knowledge base
│   ├── models.py       # Crop, Disease, AgronomyTip
│   └── management/commands/seed_crops.py
├── weather/            # Weather advisory (Stage 4)
├── market/             # Market prices (Stage 4)
├── accounts/           # Auth
├── requirements.txt
└── .env.example
```

---

## 🚀 Quick Start

### 1. Clone and set up Python environment

```bash
git clone https://github.com/yourname/agrosmart-malawi.git
cd agrosmart-malawi

python -m venv venv
source venv/bin/activate          # Linux/Mac
venv\Scripts\activate             # Windows

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
```

### 3. Set up PostgreSQL database

```sql
CREATE DATABASE agrosmart_db;
CREATE USER agrosmart_user WITH PASSWORD 'securepassword';
GRANT ALL PRIVILEGES ON DATABASE agrosmart_db TO agrosmart_user;
```

### 4. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed the crop knowledge base

```bash
python manage.py seed_crops
```

Output:
```
  Created crop: 🌽 Maize
      ✓ Created disease: Maize Streak Virus
      ✓ Created disease: Northern Leaf Blight
      ✓ Created disease: Fall Armyworm
  Created crop: 🍅 Tomato
      ✓ Created disease: Early Blight
  ...
✅ Seeded 4 crops and 9 diseases successfully.
```

### 6. Create admin user

```bash
python manage.py createsuperuser
```

### 7. Start the server

```bash
python manage.py runserver
```

### 8. Start Celery worker (for async SMS sending)

```bash
celery -A agrosmart worker --loglevel=info
```

---

## 📱 SMS Bot Flow

```
Farmer sends SMS
      │
      ▼
POST /api/sms/incoming/   ← Africa's Talking webhook
      │
      ▼
SMSProcessor.process()
      │
      ├── _detect_intent()     ← parse raw SMS text
      │         │
      │    MAIZE → crop_query
      │    1     → menu_reply
      │    HELP  → help
      │    CHICHEWA → language_ny
      │
      ├── _handle_*()          ← intent handlers
      │
      ├── Update FarmerProfile + SMSSession
      │
      └── Log to SMSLog
            │
            ▼
      send_sms_task.delay()   ← Celery async send
            │
            ▼
      Africa's Talking API → Farmer's phone
```

---

## 💬 Supported SMS Commands

| Command            | Language  | Action                        |
|--------------------|-----------|-------------------------------|
| `MAIZE`            | English   | Show maize disease menu       |
| `CHIMANGA`         | Chichewa  | Show maize disease menu       |
| `TOMATO` / `NYANYA`| Both      | Show tomato disease menu      |
| `CASSAVA` / `CHINANGWA` | Both | Show cassava disease menu    |
| `GROUNDNUT` / `NZAMA` | Both  | Show groundnut disease menu   |
| `1`, `2`, `3`...   | Both      | Select disease from menu      |
| `WEATHER LILONGWE` | English   | Weather forecast (Stage 4)    |
| `PRICE MAIZE`      | English   | Market price (Stage 4)        |
| `CHICHEWA`         | -         | Switch to Chichewa            |
| `ENGLISH`          | -         | Switch to English             |
| `HELP` / `THANDIZO`| Both      | Show all commands             |

---

## 🔌 API Endpoints

| Method | Endpoint                  | Description                  | Auth         |
|--------|---------------------------|------------------------------|--------------|
| POST   | `/api/sms/incoming/`      | Africa's Talking webhook     | None (AT)    |
| GET    | `/api/sms/farmers/`       | List all farmer profiles     | Admin        |
| GET    | `/api/sms/logs/`          | SMS message logs             | Admin        |
| POST   | `/api/sms/broadcast/`     | Send broadcast SMS           | Admin        |
| GET    | `/api/sms/stats/`         | Platform statistics          | Admin        |
| GET    | `/api/crops/`             | List all crops               | Any          |
| GET    | `/api/crops/<slug>/`      | Crop detail                  | Any          |
| GET    | `/api/crops/<slug>/diseases/` | Diseases for a crop      | Any          |
| GET    | `/api/weather/forecast/`  | Weather forecast stub        | Any          |
| GET    | `/api/market/`            | Market prices stub           | Any          |

---

## ✅ Running Tests

```bash
python manage.py test sms_bot
```

Tests cover:
- Farmer profile creation on first SMS
- Intent detection (English + Chichewa)
- Crop menu generation
- Multi-turn menu replies
- Language switching
- SMS logging
- Disease SMS formatting

---

## 🌍 Africa's Talking Setup

1. Register at https://africastalking.com
2. Create a sandbox account
3. Get your API key and set in `.env`
4. Set your webhook URL to: `https://yourdomain.com/api/sms/incoming/`
5. Use ngrok for local development: `ngrok http 8000`

---

## 📅 What's Next – Stage 3

- WhatsApp chatbot via Twilio
- React Admin Dashboard
- Expert content management UI
- Farmer analytics charts

---

*AgroSmart Malawi – Built for MACRA ICT Innovation Awards 2025*
*Empowering 4 million Malawian farmers with AI advisory*
