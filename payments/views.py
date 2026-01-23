import uuid
import hashlib
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny
from django.conf import settings

from merchants.models import MerchantAPIKey
from .models import Transaction
from .services.flutterwave import FlutterwaveService
from wallets.services import credit_pending, move_pending_to_available

logger = logging.getLogger(__name__)


class InitiatePaymentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"InitiatePaymentView POST called. Headers: {dict(request.headers)}")
        merchant = getattr(request, "merchant", None)
        logger.info(f"Merchant from middleware: {merchant}")

        # If merchant not found from secret key, check if user is authenticated
        if not merchant:
            logger.warning("No merchant found from secret key, checking user auth")
            if request.user and hasattr(request.user, 'merchant_profile') and request.user.role == 'MERCHANT':
                merchant = request.user.merchant_profile
                logger.info(f"Using authenticated user merchant: {merchant}")
            else:
                logger.error("No merchant found, returning 401")
                return Response(
                    {"error": "Unauthorized"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        amount = request.data.get("amount")
        currency = request.data.get("currency", "NGN")
        customer = request.data.get("customer")

        if not amount or not customer:
            return Response(
                {"error": "Amount and customer details are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        reference = f"TX-{uuid.uuid4().hex}"

        # Get environment from request (attached by middleware)
        environment = getattr(request, "api_key_environment", None)
        
        # If no environment from API key, allow user to specify environment or use default
        if not environment:
            environment = request.data.get("environment", "TEST").upper()
            logger.info(f"Using environment from request body: {environment}")
        
        # Create pending transaction
        transaction = Transaction.objects.create(
            merchant=merchant,
            reference=reference,
            amount=amount,
            fee=0,
            net_amount=amount,
            currency=currency,
            status="PENDING",
            payment_type="FIAT",
            provider="FLUTTERWAVE",
            environment=environment
        )

        flutterwave_payload = {
            "tx_ref": reference,
            "amount": str(amount),
            "currency": currency,
            "redirect_url": f"{settings.FRONTEND_BASE_URL}/payment-success?reference={reference}",
            "customer": customer,
            "customizations": {
                "title": merchant.business_name,
                "description": "Payment"
            }
        }

        logger.info(f"Processing payment in {environment} mode")
        
        fw_response = FlutterwaveService.initialize_payment(flutterwave_payload, environment)

        if fw_response.get("status") != "success":
            transaction.status = "FAILED"
            transaction.save()
            return Response(
                {"error": "Payment initialization failed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Store the checkout URL
        transaction.checkout_url = fw_response["data"]["link"]
        
        # Do NOT credit pending balance at initialization - wait for successful payment

        return Response(
            {
                "checkout_url": fw_response["data"]["link"],
                "reference": reference
            },
            status=status.HTTP_200_OK
        )


class ConfirmPaymentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        reference = request.data.get("reference")
        transaction_id = request.data.get("transaction_id")
        status = request.data.get("status")

        if not reference:
            return Response(
                {"error": "Reference is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            transaction = Transaction.objects.get(reference=reference)

            # 🔐 IDMPOTENCY CHECK - Prevent double processing
            if transaction.status == "SUCCESS" or transaction.balance_processed:
                return Response(
                    {"status": "already_processed", "transaction": {
                        "reference": transaction.reference,
                        "status": transaction.status,
                        "transaction_id": transaction.transaction_id
                    }},
                    status=status.HTTP_200_OK
                )

            if status == "completed" or status == "successful":
                transaction.status = "SUCCESS"
                transaction.transaction_id = transaction_id
                transaction.balance_processed = True
                transaction.save()

                # Credit merchant wallet
                from wallets.services import credit_pending, move_pending_to_available
                credit_pending(transaction.merchant, transaction.currency, transaction.amount)
                move_pending_to_available(transaction.merchant, transaction.currency, transaction.amount)

            return Response(
                {"status": "success", "transaction": {
                    "reference": transaction.reference,
                    "status": transaction.status,
                    "transaction_id": transaction.transaction_id
                }},
                status=status.HTTP_200_OK
            )

        except Transaction.DoesNotExist:
            return Response(
                {"error": "Transaction not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error confirming payment: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FlutterwaveWebhookView(APIView):
    
    permission_classes = [AllowAny]

    def verify_signature(self, request, environment="TEST"):
        signature = request.headers.get('verif-hash')
        if not signature:
            return False
            
        return FlutterwaveService.verify_webhook_signature(signature, environment)

    def post(self, request):
        # Get transaction reference from payload to determine environment
        data = request.data.get('data')
        tx_ref = data.get('tx_ref') if data else None
        
        environment = "TEST"  # Default to TEST
        if tx_ref:
            try:
                transaction = Transaction.objects.get(reference=tx_ref)
                environment = transaction.environment
                logger.info(f"Transaction {tx_ref} processed in {environment} mode")
            except Transaction.DoesNotExist:
                logger.warning(f"Transaction {tx_ref} not found, defaulting to TEST environment")

        # Verify webhook signature
        if not self.verify_signature(request, environment):
            logger.error(f"Invalid signature for transaction {tx_ref} in {environment} mode")
            return Response(
                {"error": "Invalid signature"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        event = request.data.get('event')
        data = request.data.get('data')

        if not event or not data:
            return Response(
                {"error": "Invalid payload"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get transaction reference from payload
            tx_ref = data.get('tx_ref')
            if not tx_ref:
                return Response(
                    {"error": "Transaction reference not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Find the transaction in our database
            transaction = Transaction.objects.get(reference=tx_ref)

            # Handle payment success event
            if event == 'charge.completed' and data.get('status') == 'successful':
                transaction.status = "SUCCESS"
                transaction.fee = data.get('app_fee', 0)
                transaction.net_amount = transaction.amount - transaction.fee
                transaction.metadata = data
                transaction.save()

                # Credit merchant wallet directly with available balance (not pending)
                from wallets.services import move_pending_to_available, credit_pending
                # First, ensure we have the wallet
                credit_pending(transaction.merchant, transaction.currency, transaction.amount)
                # Then move from pending to available (so it's immediately available)
                move_pending_to_available(
                    transaction.merchant,
                    transaction.currency,
                    transaction.amount
                )

            # Handle payment failed event
            elif event in ['charge.failed', 'charge.refunded']:
                transaction.status = "FAILED"
                transaction.metadata = data
                transaction.save()

                # No need to update balance since we only credited pending

            return Response({"status": "success"}, status=status.HTTP_200_OK)

        except Transaction.DoesNotExist:
            return Response(
                {"error": "Transaction not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
