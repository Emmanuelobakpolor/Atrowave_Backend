from django.urls import path
from . import views

urlpatterns = [
    # Merchant endpoints
    path('dashboard/', views.MerchantDashboardView.as_view(), name='merchant-dashboard'),
    path('kyc/submit/', views.MerchantKYCSubmitView.as_view(), name='merchant-kyc-submit'),
    path('api-keys/', views.MerchantAPIKeyView.as_view(), name='merchant-api-keys'),
    
    # Admin endpoints
    path('admin/merchants/', views.AdminMerchantListView.as_view(), name='admin-merchant-list'),
    path('admin/merchants/<int:merchant_id>/kyc/', views.AdminMerchantKYCView.as_view(), name='admin-merchant-kyc'),
    path('admin/kyc/all/', views.AdminAllKYCView.as_view(), name='admin-all-kyc'),
    path('admin/stats/', views.AdminMerchantStatsView.as_view(), name='admin-merchant-stats'),
]
