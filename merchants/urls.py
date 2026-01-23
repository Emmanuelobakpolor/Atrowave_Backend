from django.urls import path
from . import views

urlpatterns = [
    # Merchant endpoints
    path('dashboard/', views.MerchantDashboardView.as_view(), name='merchant-dashboard'),
    path('kyc/submit/', views.MerchantKYCSubmitView.as_view(), name='merchant-kyc-submit'),
    path('api-keys/', views.MerchantAPIKeyView.as_view(), name='merchant-api-keys'),
    path('api-keys/generate/', views.GenerateAPIKeyView.as_view(), name='generate-api-keys'),
    path('api-keys/regenerate/', views.RegenerateAPIKeyView.as_view(), name='regenerate-api-keys'),
    path('bank-details/', views.MerchantUpdateBankDetailsView.as_view(), name='update-bank-details'),
    path('transactions/', views.MerchantTransactionsView.as_view(), name='merchant-transactions'),
]
