from django.urls import path
from .views_bybit import bybit_webhook
from .views import flutterwave_webhook, flutterwave_payout_webhook

urlpatterns = [
    path("webhooks/bybit", bybit_webhook),
    path("webhooks/flutterwave", flutterwave_webhook),
    path("webhooks/flutterwave/payout", flutterwave_payout_webhook),
]
