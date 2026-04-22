from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.account.choices import AccountType
from apps.account.models import Account

User = get_user_model()


def validate_responsible_is_auditor(user):
    try:
        account = Account.objects.get(user=user)
    except (User.DoesNotExist, User.account.RelatedObjectDoesNotExist):
        raise ValidationError(_("Responsible user must have an account."))

    if account.account_type != AccountType.AUDITOR:
        raise ValidationError(
            _("Responsible must be a user with account type 'auditor'.")
        )
