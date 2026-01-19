from django.db import models
from django.conf import settings
import uuid
import hashlib

User = settings.AUTH_USER_MODEL


class MerchantProfile(models.Model):
    KYC_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="merchant_profile"
    )
    business_name = models.CharField(max_length=255)
    kyc_status = models.CharField(
        max_length=20,
        choices=KYC_STATUS_CHOICES,
        default="PENDING"
    )
    settlement_bank = models.CharField(max_length=255, blank=True, null=True)
    bank_account_number = models.CharField(max_length=20, blank=True, null=True)
    crypto_wallet_address = models.CharField(max_length=255, blank=True, null=True)
    is_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name

    def save(self, *args, **kwargs):
        if self.user.role != "MERCHANT":
            raise ValueError("Only users with MERCHANT role can have a merchant profile")
        super().save(*args, **kwargs)






class MerchantAPIKey(models.Model):
    ENVIRONMENT_CHOICES = (
        ("TEST", "Test"),
        ("LIVE", "Live"),
    )

    merchant = models.ForeignKey(
        MerchantProfile,
        on_delete=models.CASCADE,
        related_name="api_keys"
    )
    public_key = models.CharField(max_length=100, unique=True)
    secret_key_hash = models.CharField(max_length=128)
    environment = models.CharField(
        max_length=10,
        choices=ENVIRONMENT_CHOICES
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.merchant.business_name} - {self.environment}"

class MerchantKYC(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ("NIN", "National ID"),
        ("PASSPORT", "International Passport"),
        ("DRIVERS_LICENSE", "Driver's License"),
    )

    merchant = models.OneToOneField(
        MerchantProfile,
        on_delete=models.CASCADE,
        related_name="kyc"
    )

    # Business info
    business_type = models.CharField(
        max_length=50,
        help_text="Individual or Registered Business"
    )
    business_address = models.TextField()

    # Owner info
    owner_full_name = models.CharField(max_length=255)
    owner_date_of_birth = models.DateField()

    # Identity document
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES
    )
    document_number = models.CharField(max_length=100)
    document_image = models.ImageField(upload_to="kyc_documents/")

    # Review
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    review_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"KYC - {self.merchant.business_name}"
