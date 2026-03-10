"""Crops – URLs"""
from django.urls import path
from . import views
app_name = 'crops'
urlpatterns = [
    path('',                  views.crop_list,    name='crop_list'),
    path('<slug:slug>/',      views.crop_detail,  name='crop_detail'),
    path('<slug:slug>/diseases/', views.disease_list, name='disease_list'),
]
