from django.urls import path
from .views import price_list
urlpatterns = [path('', price_list, name='price_list')]
