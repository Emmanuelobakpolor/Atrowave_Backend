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

    @staticmethod
    def initiate_transfer(payload):
        url = f"{settings.FLUTTERWAVE_BASE_URL}/transfers"
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    @staticmethod
    def get_transfer_status(transfer_id):
        url = f"{settings.FLUTTERWAVE_BASE_URL}/transfers/{transfer_id}"
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)
        return response.json()

    @staticmethod
    def get_banks(country='NG'):
        url = f"{settings.FLUTTERWAVE_BASE_URL}/banks/{country}"
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)
        return response.json()

