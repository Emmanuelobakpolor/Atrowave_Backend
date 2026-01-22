from django.urls import path
from .views import FiatPayoutView, PayoutHistoryView, GetBanksView

urlpatterns = [
    path('fiat', FiatPayoutView.as_view(), name='fiat-payout'),
    path('', PayoutHistoryView.as_view(), name='payout-history'),
    path('banks', GetBanksView.as_view(), name='get-banks'),
]
