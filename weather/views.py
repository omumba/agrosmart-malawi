"""Weather – Stub (expanded in Stage 4)"""
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def weather_forecast(request):
    district = request.query_params.get('district', 'Lilongwe')
    return Response({
        'district': district,
        'forecast': 'Live weather integration coming in Stage 4.',
        'provider': 'OpenWeatherMap',
    })


urlpatterns = [path('forecast/', weather_forecast, name='weather_forecast')]
