"""Market – Models, Views, URLs (stub for Stage 4 expansion)"""
from django.db import models
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


class MarketPrice(models.Model):
    crop_name   = models.CharField(max_length=100)
    price_mwk   = models.DecimalField(max_digits=10, decimal_places=2, help_text="MWK per kg")
    market_name = models.CharField(max_length=100, default='Lilongwe Central Market')
    recorded_on = models.DateField(auto_now_add=True)
    updated_by  = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-recorded_on', 'crop_name']

    def __str__(self):
        return f"{self.crop_name}: MWK {self.price_mwk}/kg ({self.recorded_on})"


# ── Views ─────────────────────────────────────────────────────────────────────
@api_view(['GET'])
def price_list(request):
    """Return latest prices for all crops."""
    from django.db.models import Max
    # Get the latest price per crop
    prices = MarketPrice.objects.order_by('crop_name', '-recorded_on')
    seen = set()
    result = []
    for p in prices:
        if p.crop_name not in seen:
            seen.add(p.crop_name)
            result.append({
                'crop': p.crop_name,
                'price_mwk_per_kg': str(p.price_mwk),
                'market': p.market_name,
                'date': str(p.recorded_on),
            })
    return Response(result)


# ── URLs ──────────────────────────────────────────────────────────────────────
urlpatterns = [
    path('prices/', price_list, name='price_list'),
]
