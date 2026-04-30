from rest_framework import serializers
from apps.stock_movement.models import StockMovement


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = "__all__"
        read_only_fields = [
            "id",
            "type_of_movement",
            "quantity",
            "created_at",
            "updated_at",
        ]
