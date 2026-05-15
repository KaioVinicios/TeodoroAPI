from django import forms
from django.contrib import admin

from apps.supply_label.choices import SupplyLabelCategory, SupplyLabelType
from apps.supply_label.models import SupplyLabel


class SupplyLabelAdminForm(forms.ModelForm):
    """
    Wraps choice validation so an invalid value surfaces as a clean form
    error in the admin instead of bubbling up as a 500 (see warning in
    docs/restrictions-per-app.md about ``ValueError`` validators).
    """

    class Meta:
        model = SupplyLabel
        fields = "__all__"

    def clean_supply_label_type(self):
        value = self.cleaned_data.get("supply_label_type")
        if value not in SupplyLabelType.values:
            raise forms.ValidationError("Invalid supply type.")
        return value

    def clean_category(self):
        value = self.cleaned_data.get("category")
        if value not in SupplyLabelCategory.values:
            raise forms.ValidationError("Invalid category.")
        return value


@admin.register(SupplyLabel)
class SupplyLabelAdmin(admin.ModelAdmin):
    form = SupplyLabelAdminForm
    list_display = (
        "id",
        "name",
        "supply_label_type",
        "category",
        "details",
        "created_at",
    )
    list_filter = ("supply_label_type", "category")
    search_fields = ("name", "details")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)
