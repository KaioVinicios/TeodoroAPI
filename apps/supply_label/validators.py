from django.utils.translation import gettext_lazy as _
from apps.supply_label.choices import SupplyLabelType, SupplyLabelCategory


def validate_supply_type(value):
    if value not in SupplyLabelType.values:
        raise ValueError(_("Invalid supply type."))


def validate_category(value):
    if value not in SupplyLabelCategory.values:
        raise ValueError(_("Invalid category."))