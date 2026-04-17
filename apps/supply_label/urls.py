from django.urls import path
from apps.supply_label.views import (
    SupplyLabelListAPIView,
    SupplyLabelDetailAPIView,
)

app_name = "supply_label"

urlpatterns = [
    path("", SupplyLabelListAPIView.as_view(), name="supply_label_list"),
    path(
        "<int:pk>/",
        SupplyLabelDetailAPIView.as_view(),
        name="supply_label_detail",
    ),
]
