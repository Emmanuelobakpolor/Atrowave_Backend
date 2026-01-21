from django.db.models.signals import post_save
from django.dispatch import receiver
from merchants.models import MerchantProfile
from wallets.models import Wallet


@receiver(post_save, sender=MerchantProfile)
def create_merchant_wallets(sender, instance, created, **kwargs):
    if created:
        # Create default wallets for the new merchant
        # Fiat wallet (NGN)
        Wallet.objects.create(
            merchant=instance,
            currency='NGN',
            available_balance=0,
            pending_balance=0
        )
        # Crypto wallets (USDT, BTC, ETH)
        for currency in ['USDT', 'BTC', 'ETH']:
            Wallet.objects.create(
                merchant=instance,
                currency=currency,
                available_balance=0,
                pending_balance=0
            )
