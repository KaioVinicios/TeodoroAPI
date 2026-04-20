from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.supply_lot.choices import SupplyLotStatus


def validate_status(value):
    if value not in SupplyLotStatus.values:
        raise ValidationError(_("Invalid supply lot status."))


def validate_manufacturing_before_expiration(manufacturing_date, expiration_date):
    if manufacturing_date >= expiration_date:
        raise ValidationError(
            _("Manufacturing date must be before expiration date.")
        )
