from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.supply.models import Supply


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "supply_label",
        "status",
        "unit_of_measure",
        "quantity",
        "short_description",
        "created_at",
    )
    list_filter = ("status", "unit_of_measure", "supply_label__supply_label_type")
    search_fields = ("supply_label__name", "description")
    autocomplete_fields = ("supply_label",)
    readonly_fields = ("created_at", "updated_at", "quantity")
    fields = (
        "supply_label",
        "status",
        "unit_of_measure",
        "description",
        "quantity",
        "created_at",
        "updated_at",
    )
    ordering = ("supply_label__name",)

    @admin.display(description=_("description"))
    def short_description(self, obj):
        if not obj.description:
            return ""
        return obj.description[:60] + ("…" if len(obj.description) > 60 else "")

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)
