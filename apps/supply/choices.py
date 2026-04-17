from django.utils.translation import gettext_lazy as _

SUPPLY_STATUSES = [
    ("available", _("Available")),
    ("unavailable", _("Unavailable")),
    ("reserved", _("Reserved")),
    ("in_use", _("In Use")),
    ("depleted", _("Depleted")),
    ("damaged", _("Damaged")),
]

UNIT_OF_MEASURE_CHOICES = [
    ("unit", _("Unit")),
    ("box", _("Box")),
    ("pack", _("Pack")),
    ("bottle", _("Bottle")),
    ("liter", _("Liter")),
    ("milliliter", _("Milliliter")),
    ("gram", _("Gram")),
    ("kilogram", _("Kilogram")),
]
