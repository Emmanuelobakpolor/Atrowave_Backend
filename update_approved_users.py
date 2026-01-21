#!/usr/bin/env python3
"""Script to update existing users with KYC approved status to have is_enabled = True"""

import os
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment_gateway.settings')
django.setup()

from merchants.models import MerchantProfile

def update_approved_users():
    """Update merchants with approved KYC to be enabled"""
    print("Updating merchants with approved KYC status...")
    
    # Get all merchants with KYC approved but not enabled
    merchants = MerchantProfile.objects.filter(
        kyc_status='APPROVED',
        is_enabled=False
    )
    
    count = merchants.count()
    print(f"Found {count} merchants to update")
    
    # Update each merchant
    for merchant in merchants:
        merchant.is_enabled = True
        merchant.save()
        print(f"Updated merchant: {merchant.business_name}")
    
    print(f"Successfully updated {count} merchants")

if __name__ == "__main__":
    update_approved_users()
