from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.request.choices import RequestType
from apps.supply.models import Supply
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel


class Request(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="requests",
        verbose_name=_("user"),
    )
    request_type = models.CharField(
        max_length=20,
        choices=RequestType.choices,
        verbose_name=_("request type"),
    )
    supply = models.ForeignKey(
        Supply,
        on_delete=models.PROTECT,
        related_name="requests",
        verbose_name=_("supply"),
    )
    description = models.CharField(
        max_length=100,
        verbose_name=_("description"),
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name=_("is approved"),
    )
    approval_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("approval date"),
    )
    quantity = models.FloatField(
        verbose_name=_("quantity"),
    )

    class Meta:
        verbose_name = _("request")
        verbose_name_plural = _("requests")

    def __str__(self):
        return f"{self.request_type}"
