from django.urls import path

from apps.stock_movement.views import (
    StockMovementDetailAPIView,
    StockMovementListAPIView,
)

app_name = "stock_movement"

urlpatterns = [
    path("", StockMovementListAPIView.as_view(), name="stock_movement_list"),
    path(
        "<int:pk>/",
        StockMovementDetailAPIView.as_view(),
        name="stock_movement_detail",
    ),
]
