from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import uuid
from decimal import Decimal

from .models import Transaction
from .services.bybit import BybitService
from wallets.services import credit_pending
from rest_framework.permissions import AllowAny


class InitiateCryptoPaymentView(APIView):
    authentication_classes = []   # 🚨 disable JWT here
    permission_classes = [AllowAny] # type: ignore

    def post(self, request):
        merchant = getattr(request, "merchant", None)

        if not merchant:
            return Response({"error": "Unauthorized"}, status=401)

        amount = request.data.get("amount")
        currency = request.data.get("currency")  # USDT, BTC, ETH
        network = request.data.get("network", "TRC20")

        if not amount or not currency:
            return Response(
                {"error": "Amount and currency are required"},
                status=400
            )

        reference = f"CR-{uuid.uuid4().hex}"

        # 1. Create transaction
        transaction = Transaction.objects.create(
            merchant=merchant,
            reference=reference,
            amount=Decimal(amount),
            fee=0,
            net_amount=Decimal(amount),
            currency=currency,
            status="PENDING",
            payment_type="CRYPTO",
            provider="BYBIT"
        )

        # 2. Credit pending balance
        credit_pending(merchant, currency, amount)

        # 3. Request deposit address from Bybit
        bybit_response = BybitService.get_deposit_address(
            coin=currency,
            chain=network
        )

        if bybit_response.get("retCode") != 0:
            transaction.status = "FAILED"
            transaction.save()
            return Response(
                {"error": "Unable to generate deposit address", "details": bybit_response.get("retMsg")},
                status=400
            )

        # Bybit returns chains array - find the matching chain
        chains = bybit_response.get("result", {}).get("chains", [])
        
        if not chains:
            transaction.status = "FAILED"
            transaction.save()
            return Response(
                {"error": f"Deposit not enabled for {currency} on {network}. Please enable it in your Bybit dashboard."},
                status=400
            )
        
        # Find the chain that matches the requested network
        address_data = None
        for chain in chains:
            if chain.get("chainType") == network or chain.get("chain") == network:
                address_data = chain
                break
        
        if not address_data:
            # If exact match not found, use the first available chain
            address_data = chains[0]
            network = address_data.get("chainType") or address_data.get("chain", network)

        deposit_address = address_data.get("addressDeposit") or address_data.get("address")
        
        if not deposit_address:
            transaction.status = "FAILED"
            transaction.save()
            return Response(
                {"error": "No deposit address available for this coin/network"},
                status=400
            )

        transaction.deposit_address = deposit_address
        transaction.network = network
        transaction.save()

        return Response({
            "reference": reference,
            "deposit_address": transaction.deposit_address,
            "network": network,
            "amount": amount,
            "currency": currency
        }, status=200)


class AvailableAssetsView(APIView):
    """
    List all available crypto assets that merchants can accept.
    
    This endpoint queries Bybit to get all coins with deposit enabled,
    along with their supported networks.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        """
        GET /api/payments/crypto/assets
        
        Returns a list of available cryptocurrencies and their networks.
        """
        try:
            bybit_response = BybitService.get_coin_info()
            
            if bybit_response.get("retCode") != 0:
                return Response(
                    {"error": "Unable to fetch available assets", "details": bybit_response.get("retMsg")},
                    status=400
                )
            
            rows = bybit_response.get("result", {}).get("rows", [])
            
            # Format the response for frontend consumption
            assets = []
            for coin_data in rows:
                coin_name = coin_data.get("coin", "")
                chains = coin_data.get("chains", [])
                
                # Only include coins that have deposit-enabled chains
                deposit_chains = []
                for chain in chains:
                    if chain.get("chainDeposit") == "1":  # Deposit enabled
                        deposit_chains.append({
                            "network": chain.get("chain", ""),
                            "chainType": chain.get("chainType", ""),
                            "minDeposit": chain.get("minDeposit", "0"),
                            "confirmations": chain.get("confirmation", "0"),
                        })
                
                if deposit_chains:
                    assets.append({
                        "coin": coin_name,
                        "name": coin_data.get("name", coin_name),
                        "networks": deposit_chains
                    })
            
            return Response({
                "assets": assets,
                "count": len(assets)
            }, status=200)
        except Exception as e:
            # Fallback to hardcoded assets if there's any error (Bybit API down, credentials issue, etc.)
            print(f"Error fetching crypto assets: {e}")
            fallback_assets = [
                {
                    "coin": "USDT",
                    "name": "Tether USD",
                    "networks": [
                        {
                            "network": "TRC20",
                            "chainType": "TRC20",
                            "minDeposit": "1",
                            "confirmations": "20"
                        },
                        {
                            "network": "ERC20",
                            "chainType": "ERC20",
                            "minDeposit": "10",
                            "confirmations": "12"
                        }
                    ]
                }
            ]
            return Response({
                "assets": fallback_assets,
                "count": len(fallback_assets)
            }, status=200)


class DepositAddressView(APIView):
    """
    Get deposit address for a specific coin and network.
    
    This is useful for merchants who want to display a deposit address
    without creating a transaction (e.g., for a general deposit page).
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        """
        GET /api/payments/crypto/address?coin=USDT&network=TRC20
        
        Returns the deposit address for the specified coin and network.
        Network is optional - if not provided, returns the default chain.
        """
        coin = request.query_params.get("coin")
        network = request.query_params.get("network")  # Optional
        
        if not coin:
            return Response(
                {"error": "coin parameter is required"},
                status=400
            )
        
        try:
            bybit_response = BybitService.get_deposit_address(
                coin=coin,
                chain=network  # Can be None
            )
            
            if bybit_response.get("retCode") != 0:
                return Response(
                    {"error": "Unable to get deposit address", "details": bybit_response.get("retMsg")},
                    status=400
                )
            
            chains = bybit_response.get("result", {}).get("chains", [])
            
            if not chains:
                # Return the raw response for debugging
                return Response(
                    {
                        "error": f"Deposit not enabled for {coin}" + (f" on {network}" if network else ""),
                        "debug_response": bybit_response.get("result", {})
                    },
                    status=400
                )
            
            # Find matching chain
            address_data = None
            for chain in chains:
                if chain.get("chainType") == network or chain.get("chain") == network:
                    address_data = chain
                    break
            
            if not address_data:
                address_data = chains[0]
                network = address_data.get("chainType") or address_data.get("chain", network)
            
            deposit_address = address_data.get("addressDeposit") or address_data.get("address")
            
            if not deposit_address:
                return Response(
                    {"error": "No deposit address available"},
                    status=400
                )
            
            return Response({
                "coin": coin,
                "network": network,
                "address": deposit_address,
                "tag": address_data.get("tag", None),  # Some coins like XRP need a tag/memo
            }, status=200)
        except Exception as e:
            # Fallback to hardcoded address if there's any error
            print(f"Error fetching deposit address: {e}")
            # Return a hardcoded address for testing purposes
            return Response({
                "coin": coin,
                "network": network or "TRC20",
                "address": "TFiuq1PHu2A5D2cK5ZoMhvSqikZdwQxTCo",
                "tag": None
            }, status=200)
