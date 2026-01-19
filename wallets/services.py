from decimal import Decimal
from django.db import transaction as db_transaction
from .models import Wallet


@db_transaction.atomic
def credit_pending(merchant, currency, amount):
    wallet, _ = Wallet.objects.get_or_create(
        merchant=merchant,
        currency=currency
    )
    wallet.pending_balance += Decimal(amount)
    wallet.save()


@db_transaction.atomic
def move_pending_to_available(merchant, currency, amount):
    wallet = Wallet.objects.select_for_update().get(
        merchant=merchant,
        currency=currency
    )
    wallet.pending_balance -= Decimal(amount)
    wallet.available_balance += Decimal(amount)
    wallet.save()
