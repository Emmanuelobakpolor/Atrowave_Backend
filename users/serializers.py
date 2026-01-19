from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from merchants.models import MerchantProfile


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6)
    business_name = serializers.CharField()

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role="MERCHANT"
        )

        MerchantProfile.objects.create(
            user=user,
            business_name=validated_data["business_name"],
            kyc_status="PENDING",
            is_enabled=False
        )

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(
            email=data["email"],
            password=data["password"]
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        return user
