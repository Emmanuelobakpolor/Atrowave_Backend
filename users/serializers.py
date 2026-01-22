from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Notification
from merchants.models import MerchantProfile


class NotificationSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'created_at', 'time_ago']

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.created_at) + " ago"


class ProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='email')
    business_name = serializers.SerializerMethodField()
    kyc_status = serializers.SerializerMethodField()
    is_enabled = serializers.SerializerMethodField()
    settlement_bank = serializers.SerializerMethodField()
    bank_code = serializers.SerializerMethodField()
    bank_account_number = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'user_email', 'business_name', 'kyc_status', 'is_enabled', 
                 'settlement_bank', 'bank_code', 'bank_account_number', 'date_joined']
    
    def get_business_name(self, obj):
        if hasattr(obj, 'merchant_profile'):
            return obj.merchant_profile.business_name
        return None
    
    def get_kyc_status(self, obj):
        if hasattr(obj, 'merchant_profile'):
            return obj.merchant_profile.kyc_status
        return None
    
    def get_is_enabled(self, obj):
        if hasattr(obj, 'merchant_profile'):
            return obj.merchant_profile.is_enabled
        return None
    
    def get_settlement_bank(self, obj):
        if hasattr(obj, 'merchant_profile'):
            return obj.merchant_profile.settlement_bank
        return None
    
    def get_bank_code(self, obj):
        if hasattr(obj, 'merchant_profile'):
            return obj.merchant_profile.bank_code
        return None
    
    def get_bank_account_number(self, obj):
        if hasattr(obj, 'merchant_profile'):
            return obj.merchant_profile.bank_account_number
        return None


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
