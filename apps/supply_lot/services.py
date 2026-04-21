from django.shortcuts import get_object_or_404
from apps.supply_lot.models import SupplyLot

class SupplyLotService: 
    @staticmethod
    def list_all():
        return SupplyLot.objects.all()
    
    @staticmethod
    def get(pk):
        return get_object_or_404(SupplyLot, pk=pk)

    @staticmethod
    def create(validated_data):
        return SupplyLot.objects.create(**validated_data)
    
    @staticmethod
    def update(instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    @staticmethod
    def delete(pk):
        supply_lot = get_object_or_404(SupplyLot, pk=pk)
        supply_lot.delete()