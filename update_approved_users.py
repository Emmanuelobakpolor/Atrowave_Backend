#!/usr/bin/env python3
"""Script to update existing users with KYC approved status to have is_enabled = True"""

import os
import sys
import django

# ✅ Add project root to PYTHONPATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payment_gateway.settings")
django.setup()

from merchants.models import MerchantProfile


def update_approved_users():
    """Update merchants with approved KYC to be enabled"""
    print("Updating merchants with approved KYC status...")

    merchants = MerchantProfile.objects.filter(
        kyc_status="APPROVED",
        is_enabled=False
    )

    count = merchants.count()
    print(f"Found {count} merchants to update")

    for merchant in merchants:
        merchant.is_enabled = True
        merchant.save(update_fields=["is_enabled"])
        print(f"Updated merchant: {merchant.business_name}")

    print(f"Successfully updated {count} merchants")


if __name__ == "__main__":
    update_approved_users()
