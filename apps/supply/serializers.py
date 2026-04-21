from rest_framework import serializers

from apps.supply.models import Supply, SupplyLabel
from apps.supply.validators import (
    validate_supply_status,
    validate_supply_label_type,
    validate_quantity,
)


class SupplyLabelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = SupplyLabel
        fields = [
            "id",
            "name",
            "supply_label_type",
            "category",
            "details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_supply_label_type(self, value):
        validate_supply_label_type(value)
        return value


class SupplySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    supply_label = serializers.PrimaryKeyRelatedField(
        queryset=SupplyLabel.objects.all(),
    )
    supply_label_detail = SupplyLabelSerializer(
        source="supply_label",
        read_only=True,
    )

    class Meta:
        model = Supply
        fields = [
            "id",
            "supply_label",
            "supply_label_detail",
            "status",
            "description",
            "quantity",
            "unit_of_measure",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "supply_label_detail", "created_at", "updated_at"]

    def validate_status(self, value):
        validate_supply_status(value)
        return value

    def validate_quantity(self, value):
        validate_quantity(value)
        return value