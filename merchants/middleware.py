import hashlib
from django.http import JsonResponse
from .models import MerchantAPIKey

class MerchantAPIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth = request.headers.get("Authorization")

        if auth and auth.startswith("Bearer sk_"):
            raw_key = auth.replace("Bearer ", "")
            hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()

            try:
                api_key = MerchantAPIKey.objects.select_related("merchant").get(
                    secret_key_hash=hashed_key,
                    is_active=True,
                    merchant__is_enabled=True,
                    merchant__kyc_status="APPROVED"
                )
                request.merchant = api_key.merchant
            except MerchantAPIKey.DoesNotExist:
                return JsonResponse({"error": "Invalid API key"}, status=401)

        return self.get_response(request)
