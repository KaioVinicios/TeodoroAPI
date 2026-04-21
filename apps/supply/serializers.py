from rest_framework import serializers
from apps.supply_label.serializers import SupplyLabelSerializer

from apps.supply.models import Supply, SupplyLabel
from apps.supply.validators import (
    validate_supply_status,
    validate_supply_label_type,
    validate_quantity,
)

class SupplySerializer(serializers.ModelSerializer):

    supply_label = serializers.PrimaryKeyRelatedField(
        queryset=SupplyLabel.objects.all(),
    )
    supply_label_detail = SupplyLabelSerializer(
        source="supply_label",
        read_only=True,
    )

    class Meta:
        model = Supply
        fields = "__all__"

    def validate_status(self, value):
        validate_supply_status(value)
        return value

    def validate_quantity(self, value):
        validate_quantity(value)
        return value