from django.contrib import admin

from apps.account.models import Account
from apps.account.services import _sync_admin_flags


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "account_type",
        "organization",
        "cpf",
        "phone_number",
        "address",
        "created_at",
    )
    list_filter = ("account_type", "organization")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "cpf",
    )
    autocomplete_fields = ("user", "organization")
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "user",
        "account_type",
        "organization",
        "cpf",
        "address",
        "phone_number",
        "created_at",
        "updated_at",
    )
    ordering = ("user__username",)

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        _sync_admin_flags(obj.user, obj.account_type)
        obj.user.save(update_fields=["is_superuser", "is_staff"])
        super().save_model(request, obj, form, change)
