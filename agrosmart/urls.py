"""AgroSmart Malawi – Root URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/whatsapp/',  include('whatsapp_bot.urls')),   # ← ADD THIS

    # SMS Bot webhook (Africa's Talking posts here)
    path('api/sms/',       include('sms_bot.urls')),

    # Crop knowledge base API
    path('api/crops/',     include('crops.urls')),

    # Weather advisory API
    path('api/weather/',   include('weather.urls')),

    # Market prices API
    path('api/market/',    include('market.urls')),

    # Accounts / auth
    path('api/accounts/',  include('accounts.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Customise admin
admin.site.site_header = "AgroSmart Malawi Admin"
admin.site.site_title = "AgroSmart Admin"
admin.site.index_title = "Platform Management"
