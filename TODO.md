# TODO: Add credit_pending logic to initiate payment view

## Steps to Complete:
- [x] Modify payments/views.py to add check for balance_processed before calling credit_pending
- [x] Set balance_processed to True after successful credit_pending call
- [x] Ensure the logic is clean and integrated properly

## Progress:
- Plan approved by user
- Changes implemented successfully

## STEP 18.8: PROTECT DASHBOARD ENDPOINTS

## Steps to Complete:
- [x] Add MerchantDashboardView to merchants/views.py with permission_classes = [IsAuthenticated]
- [x] Add AdminMerchantListView and AdminMerchantKYCView for admin functionalities
- [x] Create merchants/urls.py with URL patterns
- [x] Update config/urls.py to include merchants.urls

## Progress:
- Plan approved by user
- Changes implemented successfully
