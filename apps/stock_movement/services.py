from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.stock_movement.models import StockMovement
from apps.stock_movement.validators import (
    validate_request_is_approved,
    validate_request_not_already_consumed,
    validate_supply_lots_approved,
)


class StockMovementServices:

    @staticmethod
    def list_all():
        return (
            StockMovement.objects
            .select_related("user", "supply", "request")
            .prefetch_related("supply_lots")
            .all()
        )

    @staticmethod
    def get(pk):
        return get_object_or_404(
            StockMovement.objects
            .select_related("user", "supply", "request")
            .prefetch_related("supply_lots"),
            pk=pk,
        )

    @staticmethod
    @transaction.atomic
    def create(validated_data):
        data = dict(validated_data)
        request = data["request"]
        supply_lots = data.pop("supply_lots", [])

        validate_request_is_approved(request)
        validate_request_not_already_consumed(request)
        validate_supply_lots_approved(supply_lots)

        movement = StockMovement(
            **data,
            type_of_movement=request.request_type,
            quantity=request.quantity,
        )
        movement.full_clean(exclude=["supply_lots"])
        movement.save()
        movement.supply_lots.set(supply_lots)
        return movement

    @staticmethod
    @transaction.atomic
    def update(instance, validated_data):
        if "description" in validated_data:
            instance.description = validated_data["description"]
            instance.full_clean(exclude=["supply_lots"])
            instance.save(update_fields=["description", "updated_at"])
        return instance
