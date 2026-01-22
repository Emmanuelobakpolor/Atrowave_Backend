from django.urls import path

from payments.views_crypto import (
    InitiateCryptoPaymentView,
    AvailableAssetsView,
    DepositAddressView,
)
from .views import InitiatePaymentView, FlutterwaveWebhookView

urlpatterns = [
    path("payments/initiate", InitiatePaymentView.as_view()),
    path("payments/flutterwave/webhook", FlutterwaveWebhookView.as_view()),
    path("payments/crypto/initiate", InitiateCryptoPaymentView.as_view()),
    path("payments/crypto/assets", AvailableAssetsView.as_view()),
    path("payments/crypto/address", DepositAddressView.as_view()),
]
