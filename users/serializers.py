from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from merchants.models import MerchantProfile


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6)
    business_name = serializers.CharField(required=False)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default="MERCHANT")

    def create(self, validated_data):
        role = validated_data.get("role", "MERCHANT")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=role
        )

        if role == "MERCHANT":
            business_name = validated_data.get("business_name", "Default Business")
            MerchantProfile.objects.create(
                user=user,
                business_name=business_name,
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
