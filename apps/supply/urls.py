from django.urls import path

from apps.supply.views import (
    SupplyLabelListAPIView,
    SupplyLabelDetailAPIView,
    SupplyListAPIView,
    SupplyDetailAPIView,
)

app_name = "supply"

urlpatterns = [
    # Supply Labels
    path("labels/", SupplyLabelListAPIView.as_view(), name="supply_label_list"),
    path("labels/<int:pk>/", SupplyLabelDetailAPIView.as_view(), name="supply_label_detail"),
    # Supplies
    path("", SupplyListAPIView.as_view(), name="supply_list"),
    path("<int:pk>/", SupplyDetailAPIView.as_view(), name="supply_detail"),
]