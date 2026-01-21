from django.urls import path
from . import views

urlpatterns = [
    # Merchant endpoints
    path('dashboard/', views.MerchantDashboardView.as_view(), name='merchant-dashboard'),
    path('kyc/submit/', views.MerchantKYCSubmitView.as_view(), name='merchant-kyc-submit'),
    path('api-keys/', views.MerchantAPIKeyView.as_view(), name='merchant-api-keys'),
]
