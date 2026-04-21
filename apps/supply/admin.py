from django.contrib import admin

from apps.supply.models import Supply, SupplyLabel


@admin.register(SupplyLabel)
class SupplyLabelAdmin(admin.ModelAdmin):
    list_display = ["name", "supply_label_type", "category"]
    search_fields = ["name", "category"]
    list_filter = ["supply_label_type"]


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ["supply_label", "status", "quantity", "unit_of_measure"]
    search_fields = ["supply_label__name", "description"]
    list_filter = ["status"]