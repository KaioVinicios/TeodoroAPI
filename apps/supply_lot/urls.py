from django.urls import path
from apps.supply_lot.views import SupplyLotListAPIView, SupplyLotDetailAPIView


app_name = "supply_lots"

urlpatterns = [
    path('', SupplyLotListAPIView.as_view(), name='supply_lot_list'),
    path('<int:pk>/', SupplyLotDetailAPIView.as_view(), name='supply_lot_detail')
]
