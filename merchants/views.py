from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from .models import MerchantProfile, MerchantKYC, MerchantAPIKey
from .utils import generate_api_keys
from users.models import Notification


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

        # Update merchant KYC status to under review
        merchant.kyc_status = 'UNDER_REVIEW'
        merchant.save()

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


class AdminMerchantStatsView(APIView):
    """
    Admin endpoint to get merchant statistics including total merchants and KYC status counts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'ADMIN':
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN
            )

        total_merchants = MerchantProfile.objects.count()
        pending_kyc = MerchantProfile.objects.filter(kyc_status='PENDING').count()
        under_review = MerchantProfile.objects.filter(kyc_status='UNDER_REVIEW').count()
        approved_kyc = MerchantProfile.objects.filter(kyc_status='APPROVED').count()
        rejected_kyc = MerchantProfile.objects.filter(kyc_status='REJECTED').count()

        stats = {
            "total_merchants": total_merchants,
            "kyc_status": {
                "pending": pending_kyc,
                "under_review": under_review,
                "approved": approved_kyc,
                "rejected": rejected_kyc
            }
        }

        return Response(stats, status=status.HTTP_200_OK)


class AdminAllKYCView(APIView):
    """
    Admin endpoint to view all KYC submissions from all merchants.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'ADMIN':
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN
            )

        kycs = MerchantKYC.objects.select_related('merchant__user').all()
        data = []
        for kyc in kycs:
            data.append({
                "id": kyc.id,
                "merchant_id": kyc.merchant.id,
                "business_name": kyc.merchant.business_name,
                "user_email": kyc.merchant.user.email,
                "kyc_status": kyc.merchant.kyc_status,
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

            # Create notification for account approval
            Notification.objects.create(
                user=merchant.user,
                title="Account Approved",
                message="Congratulations! Your account has been successfully approved. You can now generate live API keys and start accepting payments.",
                notification_type="ACCOUNT_APPROVED"
            )
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
        """List all API keys for the merchant (including secret keys)."""
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

        api_keys = MerchantAPIKey.objects.filter(merchant=merchant, is_active=True)
        
        # Group keys by environment
        data = {
            "test": None,
            "live": None,
        }
        
        for key in api_keys:
            env = key.environment.lower()
            if env in data:
                data[env] = {
                    "public_key": key.public_key,
                    "secret_key": key.secret_key,
                    "created_at": key.created_at.strftime("%Y-%m-%d"),
                }

        return Response(data, status=status.HTTP_200_OK)


class GenerateAPIKeyView(APIView):
    """
    Endpoint to generate a new API key pair for the merchant.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
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

        # Check if KYC is approved for live keys
        environment = request.data.get('environment', 'test')
        if environment == 'live' and merchant.kyc_status != 'APPROVED':
            return Response(
                {"error": "KYC must be approved before generating live API keys"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if merchant is enabled for live keys
        if environment == 'live' and not merchant.is_enabled:
            return Response(
                {"error": "Merchant account is not enabled for live API keys"},
                status=status.HTTP_403_FORBIDDEN
            )

        if environment not in ['test', 'live']:
            return Response(
                {"error": "Environment must be 'test' or 'live'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if merchant already has an active key for this environment
        existing_key = MerchantAPIKey.objects.filter(
            merchant=merchant,
            environment=environment.upper(),
            is_active=True
        ).first()

        if existing_key:
            return Response(
                {"error": f"You already have an active {environment} API key. Regenerate it instead."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate new API keys
        public_key, secret_key, secret_hash = generate_api_keys(environment)

        # Create the API key record
        api_key = MerchantAPIKey.objects.create(
            merchant=merchant,
            public_key=public_key,
            secret_key=secret_key,
            secret_key_hash=secret_hash,
            environment=environment.upper(),
            is_active=True
        )

        # Create notification for API key generation
        Notification.objects.create(
            user=request.user,
            title=f"{environment.title()} API Key Generated",
            message=f"Your {environment} API key has been successfully generated. You can now start accepting payments.",
            notification_type="API_KEY_GENERATED"
        )

        return Response({
            "public_key": public_key,
            "secret_key": secret_key,  # Only shown once!
            "environment": environment,
        }, status=status.HTTP_201_CREATED)


class RegenerateAPIKeyView(APIView):
    """
    Endpoint to regenerate API keys (deactivate old, create new).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'MERCHANT':
            return Response(
                {"error": "Only merchants can regenerate API keys"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            merchant = request.user.merchant_profile
        except MerchantProfile.DoesNotExist:
            return Response(
                {"error": "Merchant profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        environment = request.data.get('environment', 'test')
        if environment not in ['test', 'live']:
            return Response(
                {"error": "Environment must be 'test' or 'live'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Deactivate existing active key for this environment
        existing_keys = MerchantAPIKey.objects.filter(
            merchant=merchant,
            environment=environment.upper(),
            is_active=True
        )
        
        for key in existing_keys:
            key.is_active = False
            key.save()

        # Generate new API keys
        public_key, secret_key, secret_hash = generate_api_keys(environment)

        # Create the API key record
        api_key = MerchantAPIKey.objects.create(
            merchant=merchant,
            public_key=public_key,
            secret_key=secret_key,
            secret_key_hash=secret_hash,
            environment=environment.upper(),
            is_active=True
        )

        return Response({
            "public_key": public_key,
            "secret_key": secret_key,  # Only shown once!
            "environment": environment,
        }, status=status.HTTP_201_CREATED)
