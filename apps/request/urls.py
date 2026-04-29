from django.urls import path

from apps.request.views import (
    RequestDetailAPIView,
    RequestListAPIView,
)

app_name = "request"

urlpatterns = [
    path("", RequestListAPIView.as_view(), name="request_list"),
    path("<int:pk>/", RequestDetailAPIView.as_view(), name="request_detail"),
]
