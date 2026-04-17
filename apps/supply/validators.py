from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.supply.choices import SUPPLY_STATUSES, UNIT_OF_MEASURE_CHOICES

VALID_STATUSES = [choice[0] for choice in SUPPLY_STATUSES]
VALID_UNITS = [choice[0] for choice in UNIT_OF_MEASURE_CHOICES]


def validate_status(value):
    if value not in VALID_STATUSES:
        raise ValidationError(_("Invalid supply status."))


def validate_unit_of_measure(value):
    if value not in VALID_UNITS:
        raise ValidationError(_("Invalid unit of measure."))
