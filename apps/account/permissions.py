from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission


class IsNotCustomer(BasePermission):
    message = _("Customers cannot access this resource.")

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        account = getattr(user, "account", None)
        if account is None:
            return False

        return account.account_type != "customer"
