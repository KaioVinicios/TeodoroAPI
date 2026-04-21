from rest_framework import serializers
from apps.supply_lot.models import SupplyLot
from apps.supply_lot.validators import (
    validate_manufacturing_before_expiration, 
    validate_status
)

class SupplyLotSerializer(serializers.ModelSerializer): 

    def validate_manufacturing_before_expiration(self, value):
        validate_manufacturing_before_expiration(value)
        return value
    
    def validate_status(self, value):
        validate_status(value)
        return value
    
    class Meta: 
        model = SupplyLot
        fields = "__all__"