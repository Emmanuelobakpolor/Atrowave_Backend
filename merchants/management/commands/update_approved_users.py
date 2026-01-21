from django.core.management.base import BaseCommand
from merchants.models import MerchantProfile


class Command(BaseCommand):
    help = "Enable merchants whose KYC status is APPROVED"

    def handle(self, *args, **options):
        merchants = MerchantProfile.objects.filter(
            kyc_status="APPROVED",
            is_enabled=False
        )

        count = merchants.count()
        self.stdout.write(f"Found {count} merchants to update")

        for merchant in merchants:
            merchant.is_enabled = True
            merchant.save(update_fields=["is_enabled"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Enabled merchant: {merchant.business_name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully updated {count} merchants")
        )
