from rest_framework.permissions import BasePermission


class IsNotCustomer(BasePermission):
    message = "Customers cannot access this resource."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        account = getattr(user, "account", None)
        if account is None:
            return False

        return account.account_type != "customer"
