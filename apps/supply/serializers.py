from rest_framework import serializers
from apps.supply_label.serializers import SupplyLabelSerializer

from apps.supply.models import Supply, SupplyLabel
from apps.supply.validators import (
    validate_supply_status,
    validate_unit_of_measure,
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

    def validate_supply_status(self, value):
        validate_supply_status(value)
        return value

    def validate_unit_of_measure(self, value):
        validate_unit_of_measure(value)
        return value