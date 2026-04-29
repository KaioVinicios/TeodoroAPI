from rest_framework import serializers
from apps.request.models import Request

class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

