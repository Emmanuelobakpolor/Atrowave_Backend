import logging
from django.http import JsonResponse
from .models import MerchantAPIKey

logger = logging.getLogger(__name__)

class MerchantAPIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth = request.headers.get("Authorization")
        logger.debug(f"Authorization header received: {auth}")

        if auth and auth.startswith("Bearer sk_"):
            raw_key = auth.replace("Bearer ", "")
            logger.debug(f"Extracted raw key prefix: {raw_key[:10]}...")

            try:
                api_key = MerchantAPIKey.objects.select_related("merchant").get(
                    secret_key=raw_key,
                    is_active=True,
                    merchant__is_enabled=True,
                    merchant__kyc_status="APPROVED"
                )
                logger.debug(f"API key valid for merchant: {api_key.merchant.business_name} (ID: {api_key.merchant.id})")
                request.merchant = api_key.merchant
            except MerchantAPIKey.DoesNotExist:
                logger.error(f"API key not found or invalid. Raw key prefix: {raw_key[:10]}...")
                # Debug: Log all active API keys with their merchants for comparison
                active_keys = MerchantAPIKey.objects.select_related("merchant").filter(
                    is_active=True,
                    merchant__is_enabled=True,
                    merchant__kyc_status="APPROVED"
                )
                logger.debug(f"Active valid API keys count: {active_keys.count()}")
                for key in active_keys:
                    logger.debug(f"Stored key: {key.secret_key[:10]}..., Merchant: {key.merchant.business_name}, Status: {key.merchant.kyc_status}")
                return JsonResponse({"error": "Invalid API key"}, status=401)
        else:
            logger.debug("Authorization header missing or invalid format (expected Bearer sk_)")

        return self.get_response(request)
