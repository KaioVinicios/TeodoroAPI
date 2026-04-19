from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404

from apps.account.models import Account


class AccountServices:

    @staticmethod
    def list_all():
        return Account.objects.select_related("user", "organization").all()

    @staticmethod
    def get(pk):
        return get_object_or_404(
            Account.objects.select_related("user", "organization"),
            pk=pk,
        )

    @staticmethod
    @transaction.atomic
    def create(validated_data):
        data = dict(validated_data)
        user_data = dict(data.pop("user", {}))
        password = user_data.pop("password")
        user = User.objects.create_user(password=password, **user_data)
        account = Account(user=user, **data)
        account.full_clean()
        account.save()
        return account

    @staticmethod
    @transaction.atomic
    def update(instance, validated_data):
        data = dict(validated_data)
        user_data = dict(data.pop("user", {}))

        user = instance.user
        password = user_data.pop("password", None)
        for attr, value in user_data.items():
            setattr(user, attr, value)
        if password is not None:
            user.set_password(password)
        user.save()

        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance

    @staticmethod
    @transaction.atomic
    def delete(pk):
        account = get_object_or_404(Account, pk=pk)
        account.user.delete()
