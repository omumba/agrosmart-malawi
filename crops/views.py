"""Crops – API Views"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from .models import Crop, Disease
from .serializers import CropSerializer, DiseaseSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def crop_list(request):
    crops = Crop.objects.filter(is_active=True)
    return Response(CropSerializer(crops, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def crop_detail(request, slug):
    try:
        crop = Crop.objects.get(slug=slug, is_active=True)
    except Crop.DoesNotExist:
        return Response({'error': 'Crop not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(CropSerializer(crop).data)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def disease_list(request, slug):
    try:
        crop = Crop.objects.get(slug=slug, is_active=True)
    except Crop.DoesNotExist:
        return Response({'error': 'Crop not found'}, status=status.HTTP_404_NOT_FOUND)
    diseases = Disease.objects.filter(crop=crop, is_active=True).order_by('menu_number')
    return Response(DiseaseSerializer(diseases, many=True).data)
