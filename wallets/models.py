from django.db import models
from merchants.models import MerchantProfile


class Wallet(models.Model):
    CURRENCY_CHOICES = (
        ("NGN", "Naira"),
        ("USD", "US Dollar"),
        ("USDT", "Tether"),
        ("BTC", "Bitcoin"),
        ("ETH", "Ethereum"),
    )

    merchant = models.ForeignKey(
        MerchantProfile,
        on_delete=models.CASCADE,
        related_name="wallets"
    )
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES)
    available_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    pending_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("merchant", "currency")

    def __str__(self):
        return f"{self.merchant.business_name} - {self.currency}"
