from django.contrib import admin

from apps.organization.models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "cnpj",
        "phone_number",
        "address",
        "created_at",
    )
    search_fields = ("name", "cnpj")
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "name",
        "cnpj",
        "address",
        "phone_number",
        "created_at",
        "updated_at",
    )
    ordering = ("name",)

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)
