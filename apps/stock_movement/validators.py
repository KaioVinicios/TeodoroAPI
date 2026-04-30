from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.supply_lot.choices import SupplyLotStatus


def validate_request_is_approved(request):
    if not request.is_approved:
        raise ValidationError(
            _("Stock movement requires an approved request.")
        )


def validate_request_not_already_consumed(request):
    if hasattr(request, "stock_movement"):
        raise ValidationError(
            _("This request already has a stock movement.")
        )


def validate_supply_lots_approved(supply_lots):
    if not supply_lots:
        raise ValidationError(
            _("At least one supply lot is required.")
        )
    not_approved = [
        lot for lot in supply_lots if lot.status != SupplyLotStatus.APPROVED
    ]
    if not_approved:
        raise ValidationError(
            _("All supply lots must be approved.")
        )
