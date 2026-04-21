from rest_framework.permissions import BasePermission

from apps.account.choices import AccountType


class isAuditor(BasePermission):
    message = "Only auditors can access this resource."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        account = getattr(user, "account", None)
        if account is None:
            return False

        return account.account_type == "auditor"
