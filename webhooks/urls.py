

from django.urls import path
from .views_bybit import bybit_webhook

urlpatterns = [
    path("webhooks/bybit", bybit_webhook),
]
