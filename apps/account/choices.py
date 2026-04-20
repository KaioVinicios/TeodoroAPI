from django.db import models
from django.utils.translation import gettext_lazy as _


class AccountType(models.TextChoices):
    ADMIN = "admin", _("Administrator")
    MANAGER = "manager", _("Manager")
    TECHNICIAN = "technician", _("Technician")
    AUDITOR = "auditor", _("Auditor")
    OPERATOR = "operator", _("Operator")
    CUSTOMER = "customer", _("Customer")
