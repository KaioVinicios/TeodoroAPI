from django.db import models
from apps.core.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from apps.supply_label.validators import (
    validate_category,
    validate_supply_type,
)
from apps.supply_label.choices import (
    SUPPLY_LABEL_TYPES,
    SUPPLY_LABEL_CATEGORIES,
)


class SupplyLabel(TimeStampedModel):
    name = models.CharField(
        max_length=200,
        verbose_name=_("name"),
        blank=False,
        null=False,
    )

    supply_label_type = models.CharField(
        max_length=50,
        choices=SUPPLY_LABEL_TYPES,
        blank=False,
        null=False,
        verbose_name=_("supply type"),
        validators=[validate_supply_type],
    )

    category = models.CharField(
        max_length=50,
        choices=SUPPLY_LABEL_CATEGORIES,
        blank=False,
        null=False,
        verbose_name=_("category"),
        validators=[validate_category],
    )

    details = models.TextField(
        verbose_name=_("details"),
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.name} - {self.details}"
