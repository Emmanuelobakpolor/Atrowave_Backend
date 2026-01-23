from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Payout
from .serializers import PayoutSerializer, PayoutRequestSerializer
from wallets.models import Wallet
from merchants.models import MerchantProfile
from payments.services.flutterwave import FlutterwaveService
from django.db import transaction
from django.conf import settings
import random
import string
import logging

# Set up logger
logger = logging.getLogger(__name__)

def generate_payout_reference():
    prefix = "PO"
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{random_chars}"

class FiatPayoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        logger.info(f"Fiat payout request received from user {request.user.id}, data: {request.data}")
        
        if request.user.role != 'MERCHANT':
            logger.warning(f"Non-merchant user {request.user.id} attempted to access fiat payout endpoint")
            return Response(
                {"error": "Only merchants can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PayoutRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Validation errors for user {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            merchant = request.user.merchant_profile
            logger.info(f"Processing payout for merchant {merchant.id}, business name: {merchant.business_name}")
            
            # Validate merchant status
            if merchant.kyc_status != 'APPROVED':
                logger.warning(f"Merchant {merchant.id} with KYC status {merchant.kyc_status} attempted payout")
                return Response(
                    {"error": "Merchant must have KYC approved to request payouts"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not merchant.is_enabled:
                logger.warning(f"Disabled merchant {merchant.id} attempted payout")
                return Response(
                    {"error": "Merchant account is disabled"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate balance
            amount = serializer.validated_data['amount']
            logger.info(f"Payout amount requested: {amount} NGN")
            
            try:
                wallet = Wallet.objects.get(merchant=merchant, currency='NGN')
                logger.info(f"Wallet found: {wallet.id}, available balance: {wallet.available_balance} NGN")
            except Wallet.DoesNotExist:
                logger.error(f"NGN wallet not found for merchant {merchant.id}")
                return Response(
                    {"error": "NGN wallet not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if wallet.available_balance < amount:
                logger.error(f"Insufficient balance for merchant {merchant.id}: available {wallet.available_balance}, requested {amount}")
                return Response(
                    {"error": "Insufficient available balance"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create payout record (always PENDING)
            payout = Payout.objects.create(
                merchant=merchant,
                amount=amount,
                currency='NGN',
                status='PENDING',
                bank_details={
                    'bank_code': merchant.bank_code,
                    'account_number': f"****{merchant.bank_account_number[-4:]}",
                    'account_name': merchant.business_name
                },
                reference=generate_payout_reference()
            )
            
            # Debit available balance
            wallet.available_balance -= amount
            wallet.save()
            
            # Call Flutterwave Transfer API
            flutterwave_payload = {
                "account_bank": merchant.bank_code,
                "account_number": merchant.bank_account_number,
                "amount": str(amount),
                "narration": f"Payout {payout.reference}",
                "currency": "NGN",
                "reference": payout.reference,
                "callback_url": f"{settings.BASE_URL}/webhooks/flutterwave/payout"
            }
            
            flutterwave_response = FlutterwaveService.initiate_transfer(flutterwave_payload)
            
            # Return response immediately without waiting for transfer completion
            logger.info(f"Payout request successful for user {request.user.id}, reference: {payout.reference}")
            return Response(
                {"message": "Payout request submitted", "reference": payout.reference},
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Unexpected error processing payout for user {request.user.id}: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetBanksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            country = request.query_params.get('country', 'NG')
            banks_response = FlutterwaveService.get_banks(country)
            
            if banks_response.get('status') == 'success':
                banks = banks_response.get('data', [])
                # Return only necessary fields for selection
                simplified_banks = [
                    {
                        'id': bank.get('id'),
                        'name': bank.get('name'),
                        'code': bank.get('code'),
                        'currency': bank.get('currency')
                    } for bank in banks
                ]
                return Response(simplified_banks, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": banks_response.get('message', 'Failed to fetch banks')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PayoutHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'MERCHANT':
            return Response(
                {"error": "Only merchants can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            merchant = request.user.merchant_profile
            payouts = Payout.objects.filter(merchant=merchant).order_by('-created_at')
            serializer = PayoutSerializer(payouts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
