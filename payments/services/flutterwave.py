import requests
from django.conf import settings
import logging

# Set up logger
logger = logging.getLogger(__name__)

class FlutterwaveService:

    @staticmethod
    def get_credentials(environment):
        """Get Flutterwave credentials based on environment (TEST or LIVE)"""
        if environment == "LIVE":
            return {
                "base_url": settings.FLUTTERWAVE_LIVE_BASE_URL,
                "secret_key": settings.FLUTTERWAVE_LIVE_SECRET_KEY,
                "webhook_secret": settings.FLUTTERWAVE_LIVE_WEBHOOK_SECRET
            }
        else:  # Default to TEST
            return {
                "base_url": settings.FLUTTERWAVE_TEST_BASE_URL,
                "secret_key": settings.FLUTTERWAVE_TEST_SECRET_KEY,
                "webhook_secret": settings.FLUTTERWAVE_TEST_WEBHOOK_SECRET
            }

    @staticmethod
    def initialize_payment(payload, environment="TEST"):
        credentials = FlutterwaveService.get_credentials(environment)
        url = f"{credentials['base_url']}/payments"
        headers = {
            "Authorization": f"Bearer {credentials['secret_key']}",
            "Content-Type": "application/json"
        }

        logger.debug(f"Flutterwave initialize_payment - Environment: {environment}, URL: {url}")
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    @staticmethod
    def initiate_transfer(payload, environment="TEST"):
        credentials = FlutterwaveService.get_credentials(environment)
        url = f"{credentials['base_url']}/transfers"
        headers = {
            "Authorization": f"Bearer {credentials['secret_key']}",
            "Content-Type": "application/json"
        }

        logger.info(f"Calling Flutterwave transfer API with payload: {payload}, Environment: {environment}")
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"Flutterwave transfer API response: {response.json()}")
        
        return response.json()

    @staticmethod
    def get_transfer_status(transfer_id, environment="TEST"):
        credentials = FlutterwaveService.get_credentials(environment)
        url = f"{credentials['base_url']}/transfers/{transfer_id}"
        headers = {
            "Authorization": f"Bearer {credentials['secret_key']}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)
        return response.json()

    @staticmethod
    def get_banks(country='NG', environment="TEST"):
        credentials = FlutterwaveService.get_credentials(environment)
        url = f"{credentials['base_url']}/banks/{country}"
        headers = {
            "Authorization": f"Bearer {credentials['secret_key']}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)
        return response.json()

    @staticmethod
    def verify_webhook_signature(signature, environment="TEST"):
        """Verify webhook signature based on environment"""
        credentials = FlutterwaveService.get_credentials(environment)
        return signature == credentials['webhook_secret']

