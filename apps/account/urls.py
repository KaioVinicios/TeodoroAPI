from django.urls import path

from apps.account.views import AccountDetailAPIView, AccountListAPIView

app_name = "account"

urlpatterns = [
    path("", AccountListAPIView.as_view(), name="account_list"),
    path("<int:pk>/", AccountDetailAPIView.as_view(), name="account_detail"),
]
