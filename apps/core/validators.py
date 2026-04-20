import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_phone_number(value):
    phone = re.sub(r"\D", "", value)
    if len(phone) not in (10, 11):
        raise ValidationError(
            _("Phone number must have 10 or 11 digits (with area code).")
        )


def validate_cnpj(value):
    cnpj = re.sub(r"\D", "", value)

    if len(cnpj) != 14:
        raise ValidationError(_("CNPJ must have 14 digits."))

    if cnpj == cnpj[0] * 14:
        raise ValidationError(_("Invalid CNPJ."))

    weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights_second = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    for weights, digit_index in [(weights_first, 12), (weights_second, 13)]:
        total = sum(int(cnpj[i]) * weights[i] for i in range(len(weights)))
        remainder = total % 11
        expected = 0 if remainder < 2 else 11 - remainder
        if expected != int(cnpj[digit_index]):
            raise ValidationError(_("Invalid CNPJ."))
