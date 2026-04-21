from django.contrib import admin

from apps.supply.models import Supply

@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ["supply_label", "status", "quantity", "unit_of_measure"]
    search_fields = ["supply_label__name", "description"]
    list_filter = ["status"]