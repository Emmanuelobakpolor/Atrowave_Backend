from django.urls import path
from . import views
from payouts.views import AdminAllPayoutsView

urlpatterns = [
    # Admin endpoints
    path('merchants/', views.AdminMerchantListView.as_view(), name='admin-merchant-list'),
    path('merchants/<int:merchant_id>/kyc/', views.AdminMerchantKYCView.as_view(), name='admin-merchant-kyc'),
    path('kyc/all/', views.AdminAllKYCView.as_view(), name='admin-all-kyc'),
    path('stats/', views.AdminMerchantStatsView.as_view(), name='admin-merchant-stats'),
    path('live-api-keys/', views.AdminMerchantLiveAPIKeysView.as_view(), name='admin-live-api-keys'),
    path('transactions/all/', views.AdminAllTransactionsView.as_view(), name='admin-all-transactions'),
    path('payouts/all/', AdminAllPayoutsView.as_view(), name='admin-all-payouts'),
]
