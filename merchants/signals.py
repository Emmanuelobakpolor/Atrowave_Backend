# merchants/signals.py
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from merchants.models import MerchantProfile, MerchantAPIKey
from wallets.models import Wallet
from users.models import Notification


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


@receiver(post_save, sender=MerchantProfile)
def send_account_approved_notification(sender, instance, created, **kwargs):
    # Check if KYC status changed to APPROVED
    if not created:
        # Get previous state from database
        try:
            previous = MerchantProfile.objects.get(id=instance.id)
            if previous.kyc_status != "APPROVED" and instance.kyc_status == "APPROVED":
                # Send notification
                Notification.objects.create(
                    user=instance.user,
                    title="Account Approved",
                    message="Your merchant account has been successfully approved. You can now start accepting payments.",
                    notification_type="ACCOUNT_APPROVED"
                )
        except MerchantProfile.DoesNotExist:
            pass


@receiver(post_save, sender=MerchantAPIKey)
def send_api_key_notification(sender, instance, created, **kwargs):
    # Only send notification for LIVE environment API keys
    if instance.environment == "LIVE":
        if created:
            # New API key generated
            Notification.objects.create(
                user=instance.merchant.user,
                title="Live API Key Generated",
                message="Your live API key has been successfully generated. You can now use it for production transactions.",
                notification_type="API_KEY_GENERATED"
            )
        else:
            # Check if secret key was regenerated (we'll need to track this)
            # For now, let's assume any update to live API key is a regeneration
            Notification.objects.create(
                user=instance.merchant.user,
                title="Live API Key Regenerated",
                message="Your live API key has been regenerated. Please update your integration with the new key.",
                notification_type="API_KEY_REGENERATED"
            )
