from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.request.models import Request


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "request_type",
        "supply",
        "quantity",
        "is_approved",
        "approval_date",
        "short_description",
        "created_at",
    )
    list_filter = ("request_type", "is_approved")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "supply__supply_label__name",
        "description",
    )
    autocomplete_fields = ("user", "supply")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    @admin.display(description=_("description"))
    def short_description(self, obj):
        if not obj.description:
            return ""
        return obj.description[:60] + ("…" if len(obj.description) > 60 else "")

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)
