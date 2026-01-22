from django.urls import path
from . import views

urlpatterns = [
    # Admin endpoints
    path('merchants/', views.AdminMerchantListView.as_view(), name='admin-merchant-list'),
    path('merchants/<int:merchant_id>/kyc/', views.AdminMerchantKYCView.as_view(), name='admin-merchant-kyc'),
    path('kyc/all/', views.AdminAllKYCView.as_view(), name='admin-all-kyc'),
    path('stats/', views.AdminMerchantStatsView.as_view(), name='admin-merchant-stats'),
    path('live-api-keys/', views.AdminMerchantLiveAPIKeysView.as_view(), name='admin-live-api-keys'),
]
