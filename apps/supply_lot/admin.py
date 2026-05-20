from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.supply_lot.models import SupplyLot


@admin.register(SupplyLot)
class SupplyLotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "inspection",
        "manufacturing_date",
        "expiration_date",
        "short_description",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("description", "inspection__id")
    autocomplete_fields = ("inspection",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-manufacturing_date",)
    date_hierarchy = "expiration_date"

    @admin.display(description=_("description"))
    def short_description(self, obj):
        if not obj.description:
            return ""
        return obj.description[:60] + ("…" if len(obj.description) > 60 else "")

    def save_model(self, request, obj, form, change):
        # full_clean() runs model.clean() and enforces
        # manufacturing_date < expiration_date even though the service layer
        # currently skips it (see docs/restrictions-per-app.md).
        obj.full_clean()
        super().save_model(request, obj, form, change)
