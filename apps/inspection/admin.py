from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.inspection.models import Inspection


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "responsible",
        "is_complete",
        "completion_date",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_complete",)
    search_fields = (
        "responsible__username",
        "responsible__first_name",
        "responsible__last_name",
    )
    autocomplete_fields = ("responsible",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_complete:
            readonly += ["is_complete", "completion_date", "responsible"]
        return readonly

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_complete:
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if change:
            previous = Inspection.objects.get(pk=obj.pk)
            if previous.is_complete:
                raise ValidationError(
                    _("Cannot update an inspection that is already complete.")
                )
        obj.full_clean()
        super().save_model(request, obj, form, change)
