from django.urls import path

from apps.inspection.views import InspectionListAPIView, InspectionDetailAPIView

app_name = "inspection"

urlpatterns = [
    path("", InspectionListAPIView.as_view(), name="inspection_list"),
    path("<int:pk>/", InspectionDetailAPIView.as_view(), name="inspection_detail"),
]
