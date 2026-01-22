import hashlib
import hmac
import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from payments.models import Transaction
from wallets.models import Wallet
from wallets.services import move_pending_to_available
from webhooks.models import WebhookLog
from payouts.models import Payout

from django.db import transaction as db_transaction
from decimal import Decimal

@csrf_exempt
@require_POST
def flutterwave_payout_webhook(request):
    signature = request.headers.get("verif-hash")

    if signature != settings.FLUTTERWAVE_SECRET_KEY:
        return JsonResponse({"error": "Invalid signature"}, status=401)

    payload = json.loads(request.body)
    event = payload.get("event")
    data = payload.get("data", {})

    if event != "transfer.completed" and event != "transfer.failed":
        return JsonResponse({"status": "ignored"}, status=200)

    reference = data.get("reference")
    status = data.get("status")

    try:
        with db_transaction.atomic():
            payout = Payout.objects.select_for_update().get(
                reference=reference
            )

            # 🔐 IDMPOTENCY CHECK
            if payout.status != 'PENDING':
                return JsonResponse({"status": "already_processed"}, status=200)

            if status == "successful" or event == "transfer.completed":
                payout.status = 'SUCCESS'
            else:
                payout.status = 'FAILED'
                # Refund the balance if transfer failed
                wallet = Wallet.objects.select_for_update().get(
                    merchant=payout.merchant,
                    currency=payout.currency
                )
                wallet.available_balance += payout.amount
                wallet.save()

            payout.save()

    except Payout.DoesNotExist:
        return JsonResponse({"error": "Payout not found"}, status=404)

    return JsonResponse({"status": "ok"}, status=200)

@csrf_exempt
@require_POST
def flutterwave_webhook(request):
    signature = request.headers.get("verif-hash")

    if signature != settings.FLUTTERWAVE_SECRET_KEY:
        return JsonResponse({"error": "Invalid signature"}, status=401)

    payload = json.loads(request.body)
    event = payload.get("event")
    data = payload.get("data", {})

    if event != "charge.completed":
        return JsonResponse({"status": "ignored"}, status=200)

    reference = data.get("tx_ref")
    status = data.get("status")
    amount = Decimal(str(data.get("amount")))
    currency = data.get("currency")

    try:
        with db_transaction.atomic():
            txn = Transaction.objects.select_for_update().get(
                reference=reference
            )

            # 🔐 IDMPOTENCY CHECK
            if txn.balance_processed:
                return JsonResponse({"status": "already_processed"}, status=200)

            if status == "successful":
                txn.status = "SUCCESS"
                move_pending_to_available(
                    txn.merchant,
                    currency,
                    amount
                )
            else:
                txn.status = "FAILED"
                # Reverse pending balance
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
