from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from .models import MerchantProfile, MerchantKYC, MerchantAPIKey
from .utils import generate_api_keys


class MerchantDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'MERCHANT':
            return Response(
                {"error": "Only merchants can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            merchant = request.user.merchant_profile
            kyc_data = None
            try:
                kyc = merchant.kyc
                kyc_data = {
                    "business_type": kyc.business_type,
                    "business_address": kyc.business_address,
                    "owner_full_name": kyc.owner_full_name,
                    "document_type": kyc.document_type,
                    "submitted_at": kyc.submitted_at,
                }
            except MerchantKYC.DoesNotExist:
                kyc_data = None
            
            return Response({
                "email": request.user.email,
                "role": request.user.role,
                "business_name": merchant.business_name,
                "kyc_status": merchant.kyc_status,
                "is_enabled": merchant.is_enabled,
                "kyc_submitted": kyc_data is not None,
                "kyc_details": kyc_data,
            })
        except MerchantProfile.DoesNotExist:
            return Response(
                {"error": "Merchant profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class MerchantKYCSubmitView(APIView):
    """
    Endpoint for merchants to submit their KYC documents.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if request.user.role != 'MERCHANT':
            return Response(
                {"error": "Only merchants can submit KYC"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            merchant = request.user.merchant_profile
        except MerchantProfile.DoesNotExist:
            return Response(
                {"error": "Merchant profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if KYC already submitted
        if hasattr(merchant, 'kyc'):
            return Response(
                {"error": "KYC already submitted. Contact admin for updates."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate required fields
        required_fields = [
            'business_type', 'business_address', 'owner_full_name',
            'owner_date_of_birth', 'document_type', 'document_number', 'document_image'
        ]
        
        missing_fields = [field for field in required_fields if not request.data.get(field)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate document type
        valid_doc_types = ['NIN', 'PASSPORT', 'DRIVERS_LICENSE']
        if request.data.get('document_type') not in valid_doc_types:
            return Response(
                {"error": f"Invalid document type. Must be one of: {', '.join(valid_doc_types)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create KYC record
        kyc = MerchantKYC.objects.create(
            merchant=merchant,
            business_type=request.data.get('business_type'),
            business_address=request.data.get('business_address'),
            owner_full_name=request.data.get('owner_full_name'),
            owner_date_of_birth=request.data.get('owner_date_of_birth'),
            document_type=request.data.get('document_type'),
            document_number=request.data.get('document_number'),
            document_image=request.data.get('document_image'),
        )

        return Response({
            "message": "KYC submitted successfully. Awaiting admin review.",
            "kyc_id": kyc.id,
            "submitted_at": kyc.submitted_at,
        }, status=status.HTTP_201_CREATED)


class AdminMerchantListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'ADMIN':
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN
            )

        merchants = MerchantProfile.objects.select_related('user').all()
        data = []
        for merchant in merchants:
            data.append({
                "id": merchant.id,
                "business_name": merchant.business_name,
                "user_email": merchant.user.email,
                "kyc_status": merchant.kyc_status,
                "is_enabled": merchant.is_enabled,
                "created_at": merchant.created_at,
            })

        return Response(data, status=status.HTTP_200_OK)


class AdminMerchantKYCView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, merchant_id):
        if request.user.role != 'ADMIN':
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            merchant = MerchantProfile.objects.get(id=merchant_id)
        except MerchantProfile.DoesNotExist:
            return Response(
                {"error": "Merchant not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            kyc = merchant.kyc
            data = {
                "merchant_id": merchant.id,
                "business_name": merchant.business_name,
                "business_type": kyc.business_type,
                "business_address": kyc.business_address,
                "owner_full_name": kyc.owner_full_name,
                "owner_date_of_birth": kyc.owner_date_of_birth,
                "document_type": kyc.document_type,
                "document_number": kyc.document_number,
                "document_image": kyc.document_image.url if kyc.document_image else None,
                "submitted_at": kyc.submitted_at,
                "reviewed_at": kyc.reviewed_at,
                "review_notes": kyc.review_notes,
            }
        except MerchantKYC.DoesNotExist:
            data = {
                "merchant_id": merchant.id,
                "business_name": merchant.business_name,
                "kyc": "Not submitted"
            }

        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, merchant_id):
        """
        Admin endpoint to approve or reject merchant KYC.
        """
        if request.user.role != 'ADMIN':
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN
            )

        action = request.data.get('action')  # 'approve' or 'reject'
        review_notes = request.data.get('review_notes', '')

        if action not in ['approve', 'reject']:
            return Response(
                {"error": "Action must be 'approve' or 'reject'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            merchant = MerchantProfile.objects.get(id=merchant_id)
        except MerchantProfile.DoesNotExist:
            return Response(
                {"error": "Merchant not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            kyc = merchant.kyc
        except MerchantKYC.DoesNotExist:
            return Response(
                {"error": "KYC not submitted yet"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update KYC review
        kyc.reviewed_at = timezone.now()
        kyc.review_notes = review_notes
        kyc.save()

        # Update merchant profile
        if action == 'approve':
            merchant.kyc_status = 'APPROVED'
            merchant.is_enabled = True
            message = "Merchant KYC approved and account enabled"
        else:
            merchant.kyc_status = 'REJECTED'
            merchant.is_enabled = False
            message = "Merchant KYC rejected"

        merchant.save()

        return Response({
            "message": message,
            "merchant_id": merchant.id,
            "kyc_status": merchant.kyc_status,
            "is_enabled": merchant.is_enabled,
        }, status=status.HTTP_200_OK)


class MerchantAPIKeyView(APIView):
    """
    Endpoint for merchants to generate and manage their API keys.
    Merchants can only generate keys after KYC is approved.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all API keys for the merchant (without showing secret keys)."""
        if request.user.role != 'MERCHANT':
            return Response(
                {"error": "Only merchants can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            merchant = request.user.merchant_profile
        except MerchantProfile.DoesNotExist:
            return Response(
                {"error": "Merchant profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        api_keys = MerchantAPIKey.objects.filter(merchant=merchant)
        data = []
        for key in api_keys:
            data.append({
                "id": key.id,
                "public_key": key.public_key,
                "environment": key.environment,
                "is_active": key.is_active,
                "created_at": key.created_at,
            })

        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        """Generate a new API key pair for the merchant."""
        if request.user.role != 'MERCHANT':
            return Response(
                {"error": "Only merchants can generate API keys"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            merchant = request.user.merchant_profile
        except MerchantProfile.DoesNotExist:
            return Response(
                {"error": "Merchant profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if KYC is approved
        if merchant.kyc_status != 'APPROVED':
            return Response(
                {"error": "KYC must be approved before generating API keys"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if merchant is enabled
        if not merchant.is_enabled:
            return Response(
                {"error": "Merchant account is not enabled"},
                status=status.HTTP_403_FORBIDDEN
            )

        environment = request.data.get('environment', 'LIVE')
        if environment not in ['TEST', 'LIVE']:
            return Response(
                {"error": "Environment must be 'TEST' or 'LIVE'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if merchant already has an active key for this environment
        existing_key = MerchantAPIKey.objects.filter(
            merchant=merchant,
            environment=environment,
            is_active=True
        ).first()

        if existing_key:
            return Response(
                {"error": f"You already have an active {environment} API key. Deactivate it first to generate a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate new API keys
        public_key, secret_key, secret_hash = generate_api_keys()

        # Create the API key record
        api_key = MerchantAPIKey.objects.create(
            merchant=merchant,
            public_key=public_key,
            secret_key_hash=secret_hash,
            environment=environment,
            is_active=True
        )

        return Response({
            "message": "API keys generated successfully",
            "public_key": public_key,
            "secret_key": secret_key,  # Only shown once!
            "environment": environment,
            "warning": "SAVE YOUR SECRET KEY NOW! It will not be shown again."
        }, status=status.HTTP_201_CREATED)

    def delete(self, request):
        """Deactivate an API key."""
        if request.user.role != 'MERCHANT':
            return Response(
                {"error": "Only merchants can manage API keys"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            merchant = request.user.merchant_profile
        except MerchantProfile.DoesNotExist:
            return Response(
                {"error": "Merchant profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        key_id = request.data.get('key_id')
        if not key_id:
            return Response(
                {"error": "key_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            api_key = MerchantAPIKey.objects.get(id=key_id, merchant=merchant)
        except MerchantAPIKey.DoesNotExist:
            return Response(
                {"error": "API key not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        api_key.is_active = False
        api_key.save()

        return Response({
            "message": "API key deactivated successfully",
            "key_id": key_id,
        }, status=status.HTTP_200_OK)
