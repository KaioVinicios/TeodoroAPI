from django.db import models
from django.utils.translation import gettext_lazy as _


class SupplyStatus(models.TextChoices):
    AVAILABLE = "available", _("Available")
    UNAVAILABLE = "unavailable", _("Unavailable")
    RESERVED = "reserved", _("Reserved")
    IN_USE = "in_use", _("In Use")
    DEPLETED = "depleted", _("Depleted")
    DAMAGED = "damaged", _("Damaged")


class UnitOfMeasure(models.TextChoices):
    UNIT = "unit", _("Unit")
    BOX = "box", _("Box")
    PACK = "pack", _("Pack")
    BOTTLE = "bottle", _("Bottle")
    LITER = "liter", _("Liter")
    MILLILITER = "milliliter", _("Milliliter")
    GRAM = "gram", _("Gram")
    KILOGRAM = "kilogram", _("Kilogram")
