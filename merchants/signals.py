# merchants/signals.py
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from merchants.models import MerchantProfile
from wallets.models import Wallet


@receiver(post_save, sender=MerchantProfile)
def create_merchant_wallets(sender, instance, created, **kwargs):
    if not created:
        return

    currencies = ["NGN", "USDT", "BTC", "ETH"]

    with transaction.atomic():
        for currency in currencies:
            Wallet.objects.get_or_create(
                merchant=instance,
                currency=currency,
                defaults={
                    "available_balance": 0,
                    "pending_balance": 0,
                }
            )
