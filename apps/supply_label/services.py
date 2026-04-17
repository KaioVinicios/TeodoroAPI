from django.shortcuts import get_object_or_404
from apps.supply_label.models import SupplyLabel


class SupplyLabelServices:

    @staticmethod
    def list_all():
        return SupplyLabel.objects.all()

    @staticmethod
    def get(pk):
        return get_object_or_404(SupplyLabel, pk=pk)

    @staticmethod
    def create(validated_data):
        return SupplyLabel.objects.create(**validated_data)

    @staticmethod
    def update(instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    @staticmethod
    def delete(pk):
        supply_label = get_object_or_404(SupplyLabel, pk=pk)
        supply_label.delete()
