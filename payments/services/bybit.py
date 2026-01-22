import time
import hmac
import hashlib
import json
import requests
from django.conf import settings


class BybitService:

    @staticmethod
    def _generate_signature(timestamp, recv_window, param_str=""):
        """
        Generate Bybit API signature
        
        Args:
            timestamp: Current timestamp in milliseconds
            recv_window: Receive window (usually "5000")
            param_str: Pre-built parameter string (already sorted)
        
        Returns:
            str: HMAC SHA256 signature
        """
        # Create origin string: timestamp + api_key + recv_window + param_str
        origin_string = timestamp + settings.BYBIT_API_KEY + recv_window + param_str
        
        print("ORIGIN STRING:", origin_string)  # 👈 DEBUG
        print("PARAM STRING:", param_str)  # 👈 DEBUG
        
        signature = hmac.new(
            settings.BYBIT_API_SECRET.encode(),
            origin_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature

    @staticmethod
    def _build_param_string(params):
        """
        Build a sorted parameter string for Bybit API
        
        Bybit requires parameters to be sorted alphabetically by key.
        This method ensures consistent ordering between signature and request.
        
        Args:
            params: Dictionary of parameters
            
        Returns:
            str: URL-encoded parameter string (sorted alphabetically)
        """
        if not params:
            return ""
        
        # Sort by key alphabetically (Bybit uses standard alphabetical sort)
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        return '&'.join([f"{k}={v}" for k, v in sorted_params])

    @staticmethod
    def _headers(param_str=""):
        """
        Generate headers with signature
        
        Args:
            param_str: Pre-built parameter string to include in signature
        
        Returns:
            dict: Headers for Bybit API request
        """
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        
        signature = BybitService._generate_signature(timestamp, recv_window, param_str)

        return {
            "X-BAPI-API-KEY": settings.BYBIT_API_KEY,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "Content-Type": "application/json",
        }

    @staticmethod
    def get_deposit_address(coin: str, chain: str = None):
        """
        Get deposit address for a specific coin and chain
        
        Args:
            coin: The cryptocurrency (e.g., "USDT")
            chain: The blockchain network (e.g., "TRC20", "TRON", "ETH")
            
        Returns:
            dict: Bybit API response containing the deposit address
        """
        try:
            base_url = f"{settings.BYBIT_BASE_URL}/v5/asset/deposit/query-address"

            # Build params dict - only include coin, chainType is optional
            params = {"coin": coin}
            
            # chainType is optional - if provided, add it
            if chain:
                params["chainType"] = chain
            
            # Build sorted parameter string - this MUST match what's in the URL
            param_str = BybitService._build_param_string(params)
            
            # Build full URL with query string (using our sorted param string)
            url = f"{base_url}?{param_str}"
            
            # Generate headers with the same param string used in URL
            headers = BybitService._headers(param_str)
            
            print("FULL URL:", url)  # 👈 DEBUG

            # Make request WITHOUT params argument (we already added them to URL)
            response = requests.get(
                url,
                headers=headers,
                timeout=15,
            )

            result = response.json()
            print("BYBIT RAW:", result)
            
            # The API returns the address directly in result for single chain coins
            # or in chains array for multi-chain coins
            # Normalize the response to always have a consistent structure
            if result.get("retCode") == 0:
                res = result.get("result", {})
                # If chains is empty but we have a direct address, create chains array
                if not res.get("chains") and res.get("address"):
                    result["result"]["chains"] = [{
                        "chainType": res.get("chainType", chain or ""),
                        "chain": res.get("chain", chain or ""),
                        "addressDeposit": res.get("address", ""),
                        "address": res.get("address", ""),
                        "tag": res.get("tag", ""),
                    }]
            
            return result
        except Exception as e:
            print(f"Bybit API error (get_deposit_address): {e}")
            # Return a default error response
            return {
                "retCode": 1,
                "retMsg": str(e),
                "result": {}
            }

    @staticmethod
    def get_coin_info():
        """
        Get all available coins and their deposit/withdrawal info
        
        This returns all coins enabled on your Bybit account with their
        supported networks/chains.
        
        Returns:
            dict: Bybit API response containing coin information
        """
        try:
            base_url = f"{settings.BYBIT_BASE_URL}/v5/asset/coin/query-info"
            
            # No params needed for this endpoint
            param_str = ""
            url = base_url
            
            headers = BybitService._headers(param_str)
            
            response = requests.get(
                url,
                headers=headers,
                timeout=15,
            )

            return response.json()
        except Exception as e:
            print(f"Bybit API error (get_coin_info): {e}")
            # Return a default error response
            return {
                "retCode": 1,
                "retMsg": str(e),
                "result": {}
            }

    @staticmethod
    def get_deposit_records(coin: str = None, limit: int = 50):
        """
        Get deposit records to match incoming payments
        
        Args:
            coin: Optional - filter by specific coin (e.g., "USDT")
            limit: Number of records to return (default 50)
            
        Returns:
            dict: Bybit API response containing deposit records
        """
        base_url = f"{settings.BYBIT_BASE_URL}/v5/asset/deposit/query-record"
        
        params = {"limit": str(limit)}
        if coin:
            params["coin"] = coin
        
        param_str = BybitService._build_param_string(params)
        url = f"{base_url}?{param_str}"
        
        headers = BybitService._headers(param_str)
        
        response = requests.get(
            url,
            headers=headers,
            timeout=15,
        )

        return response.json()
