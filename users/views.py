import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated

from .serializers import RegisterSerializer, LoginSerializer, ProfileSerializer
from .models import User, PasswordResetToken


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {"message": "Account created successfully"},
            status=status.HTTP_201_CREATED
        )


class RegisterAdminView(APIView):
    """
    Endpoint to register an admin user.
    This should be used cautiously and only in development or with proper security.
    """
    def post(self, request):
        # For security, you might want to add additional checks here
        # For example, check if there's already an admin user, or require a secret key
        
        data = request.data.copy()
        data["role"] = "ADMIN"
        
        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Make sure admin user has staff and superuser privileges
        user.is_staff = True
        user.is_superuser = True
        user.save()

        return Response(
            {"message": "Admin account created successfully"},
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": user.role,
        })


class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            return Response(
                {"message": "If the email exists, a reset link has been sent"},
                status=status.HTTP_200_OK
            )

        # Delete any existing tokens for this user
        PasswordResetToken.objects.filter(user=user).delete()

        # Create new token
        token = str(uuid.uuid4())
        reset_token = PasswordResetToken.objects.create(
            user=user,
            token=token
        )

        # Send email
        reset_url = f"http://localhost:8000/api/auth/reset-password/{token}"
        subject = "Password Reset Request"
        message = f"Click the link to reset your password: {reset_url}"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

        return Response(
            {"message": "If the email exists, a reset link has been sent"},
            status=status.HTTP_200_OK
        )


class ResetPasswordView(APIView):
    def post(self, request, token):
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        if not password or not confirm_password:
            return Response(
                {"error": "Password and confirm password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if password != confirm_password:
            return Response(
                {"error": "Passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            reset_token = PasswordResetToken.objects.get(token=token)
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if reset_token.is_expired():
            reset_token.delete()
            return Response(
                {"error": "Token has expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update password
        user = reset_token.user
        user.set_password(password)
        user.save()

        # Delete the token
        reset_token.delete()

        return Response(
            {"message": "Password reset successfully"},
            status=status.HTTP_200_OK
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not current_password or not new_password or not confirm_password:
            return Response(
                {"error": "All password fields are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {"error": "New passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        # Check current password
        if not user.check_password(current_password):
            return Response(
                {"error": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update password
        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password changed successfully"},
            status=status.HTTP_200_OK
        )


from rest_framework.permissions import IsAuthenticated

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            serializer = ProfileSerializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            import logging
            logging.error(f"ProfileView error: {str(e)}")
            import traceback
            logging.error(f"Stack trace: {traceback.format_exc()}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
