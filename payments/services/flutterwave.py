import requests
from django.conf import settings

class FlutterwaveService:

    @staticmethod
    def initialize_payment(payload):
        url = f"{settings.FLUTTERWAVE_BASE_URL}/payments"
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()
