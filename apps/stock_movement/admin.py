from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.stock_movement.models import StockMovement
from apps.stock_movement.validators import (
    validate_request_is_approved,
    validate_request_not_already_consumed,
    validate_supply_lots_approved,
)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "type_of_movement",
        "user",
        "supply",
        "quantity",
        "request",
        "short_description",
        "created_at",
    )
    list_filter = ("type_of_movement",)
    search_fields = (
        "user__username",
        "supply__supply_label__name",
        "description",
    )
    autocomplete_fields = ("user", "supply", "request")
    filter_horizontal = ("supply_lots",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    @admin.display(description=_("description"))
    def short_description(self, obj):
        if not obj.description:
            return ""
        return obj.description[:60] + ("…" if len(obj.description) > 60 else "")

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            # Once created, only ``description`` is mutable.
            readonly += [
                "type_of_movement",
                "user",
                "supply",
                "request",
                "quantity",
            ]
        return readonly

    def save_model(self, request, obj, form, change):
        if not change:
            validate_request_is_approved(obj.request)
            validate_request_not_already_consumed(obj.request)
            obj.type_of_movement = obj.request.request_type
            obj.quantity = obj.request.quantity
        obj.full_clean(exclude=["supply_lots"])
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not change:
            validate_supply_lots_approved(list(form.instance.supply_lots.all()))
