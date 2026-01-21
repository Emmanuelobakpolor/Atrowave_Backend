from django.urls import path
from .views import WalletsView, TransactionsView

urlpatterns = [
    path('wallets/', WalletsView.as_view(), name='wallets'),
    path('transactions/', TransactionsView.as_view(), name='transactions'),
]
