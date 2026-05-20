from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission

from apps.account.choices import AccountType


class IsAuditor(BasePermission):
    message = _("Only auditors can access this resource.")

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        account = getattr(user, "account", None)
        if account is None:
            return False

        return account.account_type == AccountType.AUDITOR


class IsAuditorOrAdmin(BasePermission):
    message = _("Only auditors or admins can access this resource.")

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        account = getattr(user, "account", None)
        if account is None:
            return False

        return account.account_type in (AccountType.AUDITOR, AccountType.ADMIN)
