"""
Run this once on Railway to create a superuser.
Called from railway.toml start command.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrosmart.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@agrosmart.mw')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')

if not password:
    print("⚠️  DJANGO_SUPERUSER_PASSWORD not set, skipping superuser creation")
elif User.objects.filter(username=username).exists():
    print(f"✅ Superuser '{username}' already exists")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superuser '{username}' created successfully")
