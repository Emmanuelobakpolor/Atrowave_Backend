import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny
from .models import Transaction
from .services.flutterwave import FlutterwaveService
from wallets.services import credit_pending


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
            "redirect_url": "https://your-redirect-url.com",
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
