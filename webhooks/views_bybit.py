import hmac
import hashlib
import json
from decimal import Decimal

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction as db_transaction

from payments.models import Transaction
from wallets.models import Wallet

def verify_bybit_signature(headers, body):
    signature = headers.get("X-BAPI-SIGN")
    timestamp = headers.get("X-BAPI-TIMESTAMP")

    if not signature or not timestamp:
        return False

    payload = timestamp + body
    expected = hmac.new(
        settings.BYBIT_API_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)

@csrf_exempt
@require_POST
def bybit_webhook(request):
    body = request.body.decode()

    if not verify_bybit_signature(request.headers, body):
        return JsonResponse({"error": "Invalid signature"}, status=401)

    payload = json.loads(body)
    event = payload.get("event")

    # We only care about deposits
    if event != "deposit":
        return JsonResponse({"status": "ignored"}, status=200)

    data = payload.get("data", {})
    address = data.get("address")
    amount = Decimal(str(data.get("amount")))
    currency = data.get("coin")
    tx_hash = data.get("txHash")
    status = data.get("status")  # success / failed

    try:
        with db_transaction.atomic():
            # Match transaction by deposit address
            txn = Transaction.objects.select_for_update().get(
                deposit_address=address,
                status="PENDING",
                payment_type="CRYPTO",
                provider="BYBIT"
            )

            # 🔐 IDMPOTENCY CHECK
            if txn.balance_processed:
                return JsonResponse({"status": "already_processed"}, status=200)

            if status == "success":
                txn.status = "SUCCESS"
                txn.tx_hash = tx_hash

                # Move pending → available
                wallet = Wallet.objects.select_for_update().get(
                    merchant=txn.merchant,
                    currency=currency
                )
                wallet.pending_balance -= amount
                wallet.available_balance += amount
                wallet.save()

            else:
                txn.status = "FAILED"

                # Reverse pending
                wallet = Wallet.objects.select_for_update().get(
                    merchant=txn.merchant,
                    currency=currency
                )
                wallet.pending_balance -= amount
                wallet.save()

            txn.balance_processed = True
            txn.save()

    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found"}, status=404)

    return JsonResponse({"status": "ok"}, status=200)
