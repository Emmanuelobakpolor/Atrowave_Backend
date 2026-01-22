from rest_framework import serializers
from .models import Payout

class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = ['id', 'amount', 'currency', 'status', 'reference', 'created_at', 'processed_at']
        read_only_fields = ['id', 'status', 'reference', 'created_at', 'processed_at']

class PayoutRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
