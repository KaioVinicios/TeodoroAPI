from django.db import models
from apps.request.choices import RequestType
from apps.supply.models import Supply
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel


class Request(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="requests")
    request_type = models.CharField(
        max_length=20,
        choices=RequestType.choices,
    )
    supply = models.ForeignKey(Supply, on_delete=models.PROTECT, related_name="requests")
    description = models.CharField(max_length=100)
    is_approved = models.BooleanField(default=False)
    approval_date = models.DateField(null=True, blank=True)
    quantity = models.FloatField()

    def __str__(self):
        return f"{self.request_type}"
