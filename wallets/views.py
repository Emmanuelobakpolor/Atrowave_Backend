from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Wallet
from payments.models import Transaction


class WalletsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'MERCHANT':
            return Response(
                {"error": "Only merchants can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            merchant = request.user.merchant_profile
            wallets = Wallet.objects.filter(merchant=merchant)
            
            wallet_data = []
            for wallet in wallets:
                # Determine type based on currency
                if wallet.currency == 'NGN':
                    wallet_type = 'FIAT'
                else:
                    wallet_type = 'CRYPTO'
                
                wallet_data.append({
                    "currency": wallet.currency,
                    "available_balance": str(wallet.available_balance),
                    "pending_balance": str(wallet.pending_balance),
                    "type": wallet_type
                })
            
            return Response(wallet_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'MERCHANT':
            return Response(
                {"error": "Only merchants can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            merchant = request.user.merchant_profile
            transactions = Transaction.objects.filter(merchant=merchant).order_by('-created_at')
            
            transaction_data = []
            for tx in transactions:
                transaction_data.append({
                    "reference": tx.reference,
                    "amount": str(tx.amount),
                    "currency": tx.currency,
                    "status": tx.status,
                    "payment_type": tx.payment_type,
                    "created_at": tx.created_at.isoformat(),
                    "provider": tx.provider,
                    "environment": tx.environment
                })
            
            return Response(transaction_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
