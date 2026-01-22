from django.db import models
from merchants.models import MerchantProfile
from django.utils import timezone

class Payout(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    merchant = models.ForeignKey(MerchantProfile, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    bank_details = models.JSONField(null=True, blank=True)  # Store bank account details as JSON
    reference = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payout {self.reference} - {self.status}"
