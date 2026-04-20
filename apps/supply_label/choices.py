from django.contrib import models
from django.utils.translation import gettext_lazy as _


class SupplyLabelType(models.TextChoices):
    MEDICATION = "medication", _("Medication")
    EQUIPMENT = "equipment", _("Equipment")
    STERILIZATION = "sterilization", _("Sterilization")
    NUTRITION = "nutrition", _("Nutrition")
    BLOOD_PRODUCT = "blood_product", _("Blood Product")
    OTHER = "other", _("Other")


class SupplyLabelCategory(models.TextChoices):
    DISPOSABLE = "disposable", _("Disposable")
    REUSABLE = "reusable", _("Reusable")
    IMPLANTABLE = "implantable", _("Implantable")
    DIAGNOSTIC = "diagnostic", _("Diagnostic")
    THERAPEUTIC = "therapeutic", _("Therapeutic")
    OTHER = "other", _("Other")
