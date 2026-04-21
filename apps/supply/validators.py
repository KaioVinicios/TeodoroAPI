from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.supply.choices import SupplyStatus, UnitOfMeasure


def validate_status(value):
    if value not in SupplyStatus.values:
        raise ValidationError(_("Invalid supply status."))


def validate_unit_of_measure(value):
    if value not in UnitOfMeasure.values:
        raise ValidationError(_("Invalid unit of measure."))
