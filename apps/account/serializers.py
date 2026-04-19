from django.contrib.auth.models import User
from rest_framework import serializers

from apps.account.models import Account
from apps.account.validators import validate_account_type, validate_cpf
from apps.core.validators import validate_phone_number
from apps.organization.models import Organization


class AccountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    username = serializers.CharField(max_length=150, source="user.username")
    password = serializers.CharField(
        write_only=True, min_length=8, source="user.password"
    )
    email = serializers.EmailField(source="user.email")
    first_name = serializers.CharField(
        max_length=150, allow_blank=True, required=False, source="user.first_name"
    )
    last_name = serializers.CharField(
        max_length=150, allow_blank=True, required=False, source="user.last_name"
    )

    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Account
        fields = [
            "id",
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
            "account_type",
            "cpf",
            "address",
            "phone_number",
            "organization",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_account_type(self, value):
        validate_account_type(value)
        return value

    def validate_cpf(self, value):
        validate_cpf(value)
        return value

    def validate_phone_number(self, value):
        validate_phone_number(value)
        return value

    def validate_username(self, value):
        qs = User.objects.filter(username=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def validate_email(self, value):
        qs = User.objects.filter(email=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value
