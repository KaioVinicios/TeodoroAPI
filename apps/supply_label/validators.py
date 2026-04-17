from django.utils.translation import gettext_lazy as _
from apps.supply_label.choices import (
    SUPPLY_LABEL_TYPES,
    SUPPLY_LABEL_CATEGORIES,
)

VALID_TYPES = [choice[0] for choice in SUPPLY_LABEL_TYPES]
VALID_CATEGORIES = [choice[0] for choice in SUPPLY_LABEL_CATEGORIES]


def validate_supply_type(value):
    if value not in VALID_TYPES:
        raise ValueError(_("Invalid supply type."))


def validate_category(value):
    if value not in VALID_CATEGORIES:
        raise ValueError(_("Invalid category."))
