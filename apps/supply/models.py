from django.db import models
from django.db.models import Sum
from apps.core.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from apps.supply_label.models import SupplyLabel
from apps.supply.choices import SupplyStatus, UnitOfMeasure
from apps.supply.validators import validate_status, validate_unit_of_measure
from apps.supply_lot.choices import SupplyLotStatus


class Supply(TimeStampedModel):
    supply_label = models.ForeignKey(
        SupplyLabel,
        on_delete=models.PROTECT,
        related_name="supplies",
        verbose_name=_("supply label"),
    )
    status = models.CharField(
        max_length=20,
        choices=SupplyStatus.choices,
        default=SupplyStatus.AVAILABLE,
        verbose_name=_("status"),
        validators=[validate_status],
    )
    description = models.TextField(
        verbose_name=_("description"),
    )
    unit_of_measure = models.CharField(
        max_length=20,
        choices=UnitOfMeasure.choices,
        verbose_name=_("unit of measure"),
        validators=[validate_unit_of_measure],
    )

    # Only accepts approved supply lots for stock movements
    @property
    def quantity(self):
        approved_movements = self.stock_movements.filter(
            pk__in=self.stock_movements.filter(
                supply_lots__status=SupplyLotStatus.APPROVED
            ).values("pk")
        )
        return approved_movements.aggregate(total=Sum("quantity"))["total"] or 0

    class Meta:
        verbose_name = _("supply")
        verbose_name_plural = _("supplies")
        ordering = ["supply_label__name"]

    def __str__(self):
        return f"{self.supply_label.name} — {self.get_status_display()}"
