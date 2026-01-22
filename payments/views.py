import uuid
import hashlib
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny
from django.conf import settings
from .models import Transaction
from .services.flutterwave import FlutterwaveService
from wallets.services import credit_pending, move_pending_to_available


class NoAuth(BaseAuthentication):
    def authenticate(self, request):
        return None


class InitiatePaymentView(APIView):
    authentication_classes = [NoAuth]
    permission_classes = [AllowAny]

    def post(self, request):
        merchant = getattr(request, "merchant", None)

        if not merchant:
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
            provider="FLUTTERWAVE"
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

        fw_response = FlutterwaveService.initialize_payment(flutterwave_payload)

        if fw_response.get("status") != "success":
            transaction.status = "FAILED"
            transaction.save()
            return Response(
                {"error": "Payment initialization failed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Credit pending only once
        if not transaction.balance_processed:
            credit_pending(merchant, currency, amount)
            transaction.balance_processed = True
            transaction.save()

        return Response(
            {
                "checkout_url": fw_response["data"]["link"],
                "reference": reference
            },
            status=status.HTTP_200_OK
        )


class FlutterwaveWebhookView(APIView):
    authentication_classes = [NoAuth]
    permission_classes = [AllowAny]

    def verify_signature(self, request):
        signature = request.headers.get('verif-hash')
        if not signature:
            return False
            
        return signature == settings.FLUTTERWAVE_WEBHOOK_SECRET

    def post(self, request):
        # Verify webhook signature
        if not self.verify_signature(request):
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

                # Move pending balance to available
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
