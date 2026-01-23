from django.db import models
from merchants.models import MerchantProfile


class Transaction(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    )

    PAYMENT_TYPE = (
        ("FIAT", "Fiat"),
        ("CRYPTO", "Crypto"),
    )

    PROVIDER_CHOICES = (
        ("FLUTTERWAVE", "Flutterwave"),
        ("BYBIT", "Bybit"),
    )

    ENVIRONMENT_CHOICES = (
        ("TEST", "Test"),
        ("LIVE", "Live"),
    )

    merchant = models.ForeignKey(
        MerchantProfile,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    environment = models.CharField(
        max_length=10,
        choices=ENVIRONMENT_CHOICES,
        default="TEST"
    )
    metadata = models.JSONField(blank=True, null=True)
    checkout_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    balance_processed = models.BooleanField(default=False)
    deposit_address = models.CharField(max_length=255, blank=True, null=True)
    network = models.CharField(max_length=50, blank=True, null=True)
    tx_hash = models.CharField(max_length=255, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)


    def __str__(self):
        return self.reference
