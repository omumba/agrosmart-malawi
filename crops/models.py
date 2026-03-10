"""
Crops App – Models
Knowledge base: crop types, diseases, pests, treatments, advice.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Crop(models.Model):
    """A crop grown by Malawian farmers."""

    name_en = models.CharField(max_length=100, verbose_name="Name (English)")
    name_ny = models.CharField(max_length=100, verbose_name="Name (Chichewa)", blank=True)
    slug    = models.SlugField(unique=True, help_text="SMS keyword, e.g. 'maize'")
    description_en = models.TextField(blank=True)
    description_ny = models.TextField(blank=True)
    icon    = models.CharField(max_length=10, default='🌱')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name_en']
        verbose_name = 'Crop'
        verbose_name_plural = 'Crops'

    def __str__(self):
        return self.name_en

    def get_name(self, lang='en'):
        return self.name_ny if lang == 'ny' and self.name_ny else self.name_en


class Disease(models.Model):
    """A disease, pest, or nutritional deficiency affecting a crop."""

    CATEGORY_CHOICES = [
        ('fungal',      'Fungal Disease'),
        ('viral',       'Viral Disease'),
        ('bacterial',   'Bacterial Disease'),
        ('pest',        'Pest / Insect'),
        ('deficiency',  'Nutrient Deficiency'),
        ('other',       'Other'),
    ]
    SEVERITY_CHOICES = [
        ('low',      'Low'),
        ('medium',   'Medium'),
        ('high',     'High'),
        ('critical', 'Critical'),
    ]

    crop         = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='diseases')
    name_en      = models.CharField(max_length=150)
    name_ny      = models.CharField(max_length=150, blank=True)
    category     = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    severity     = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    menu_number  = models.PositiveSmallIntegerField(
        help_text="Number farmers type in SMS menu (1, 2, 3...)"
    )

    # Symptoms
    symptoms_en  = models.TextField(help_text="Visible symptoms in English")
    symptoms_ny  = models.TextField(blank=True, help_text="Visible symptoms in Chichewa")

    # Treatment
    treatment_en = models.TextField(help_text="Recommended treatment in English")
    treatment_ny = models.TextField(blank=True, help_text="Recommended treatment in Chichewa")

    # Prevention
    prevention_en = models.TextField(blank=True)
    prevention_ny = models.TextField(blank=True)

    # Optional: recommended product
    recommended_product = models.CharField(max_length=200, blank=True)

    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='disease_updates'
    )

    class Meta:
        ordering = ['crop', 'menu_number']
        unique_together = [['crop', 'menu_number']]
        verbose_name = 'Disease / Pest'
        verbose_name_plural = 'Diseases & Pests'

    def __str__(self):
        return f"{self.crop.name_en} – {self.name_en}"

    def get_name(self, lang='en'):
        return self.name_ny if lang == 'ny' and self.name_ny else self.name_en

    def get_symptoms(self, lang='en'):
        return self.symptoms_ny if lang == 'ny' and self.symptoms_ny else self.symptoms_en

    def get_treatment(self, lang='en'):
        return self.treatment_ny if lang == 'ny' and self.treatment_ny else self.treatment_en

    def format_sms_response(self, lang='en') -> str:
        """Return a ≤160-char-friendly SMS treatment response."""
        icon = {'fungal': '🍄', 'viral': '🦠', 'pest': '🐛', 'bacterial': '🔬'}.get(self.category, '⚠️')
        crop_name = self.crop.get_name(lang)
        disease_name = self.get_name(lang)
        treatment = self.get_treatment(lang)

        lines = [f"{icon} {crop_name}: {disease_name}", ""]
        lines += [f"• {line.strip()}" for line in treatment.split('\n') if line.strip()]
        if self.recommended_product:
            lines.append(f"\nProduct: {self.recommended_product}")
        return '\n'.join(lines)


class AgronomyTip(models.Model):
    """General farming tips pushed to farmers as broadcasts."""

    SEASON_CHOICES = [
        ('planting',   'Planting Season'),
        ('growing',    'Growing Season'),
        ('harvest',    'Harvest Season'),
        ('any',        'Any Time'),
    ]

    crop     = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='tips', null=True, blank=True)
    title_en = models.CharField(max_length=200)
    title_ny = models.CharField(max_length=200, blank=True)
    body_en  = models.TextField()
    body_ny  = models.TextField(blank=True)
    season   = models.CharField(max_length=20, choices=SEASON_CHOICES, default='any')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title_en
