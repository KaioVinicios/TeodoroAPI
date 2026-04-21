from django.db import transaction
from django.shortcuts import get_object_or_404

from apps.supply.models import Supply, SupplyLabel


class SupplyLabelServices:

    @staticmethod
    def list_all():
        return SupplyLabel.objects.all()

    @staticmethod
    def get(pk):
        return get_object_or_404(SupplyLabel, pk=pk)

    @staticmethod
    @transaction.atomic
    def create(validated_data):
        label = SupplyLabel(**validated_data)
        label.full_clean()
        label.save()
        return label

    @staticmethod
    @transaction.atomic
    def update(instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance

    @staticmethod
    @transaction.atomic
    def delete(pk):
        label = get_object_or_404(SupplyLabel, pk=pk)
        label.delete()


class SupplyServices:

    @staticmethod
    def list_all():
        return Supply.objects.select_related("supply_label").all()

    @staticmethod
    def get(pk):
        return get_object_or_404(
            Supply.objects.select_related("supply_label"),
            pk=pk,
        )

    @staticmethod
    @transaction.atomic
    def create(validated_data):
        supply = Supply(**validated_data)
        supply.full_clean()
        supply.save()
        return supply

    @staticmethod
    @transaction.atomic
    def update(instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance

    @staticmethod
    @transaction.atomic
    def delete(pk):
        supply = get_object_or_404(Supply, pk=pk)
        supply.delete()