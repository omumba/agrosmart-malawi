from django.db import models
class WeatherAlert(models.Model):
    district = models.CharField(max_length=100)
    message  = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
