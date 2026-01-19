from django.contrib import admin


from .models import MerchantAPIKey, MerchantProfile

@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    list_display = ("business_name", "kyc_status", "is_enabled", "created_at")
    list_filter = ("kyc_status", "is_enabled")
    search_fields = ("business_name",)


@admin.register(MerchantAPIKey)
class MerchantAPIKeyAdmin(admin.ModelAdmin):
    list_display = ("merchant", "environment", "is_active", "created_at")
    list_filter = ("environment", "is_active")
    search_fields = ("merchant__business_name",)
    
from .models import MerchantKYC

@admin.register(MerchantKYC)
class MerchantKYCAdmin(admin.ModelAdmin):
    list_display = (
        "merchant",
        "submitted_at",
        "reviewed_at",
    )
    search_fields = ("merchant__business_name",)
