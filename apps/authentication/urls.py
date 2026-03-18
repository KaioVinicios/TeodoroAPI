from django.urls import path
from apps.authentication.views import (
    CookieObtainPairView,
    CookieRefreshTokenView,
    CookieTokenVerifyView,
    CookieLogoutView,
)

urlpatterns = [
    path("logout/", CookieLogoutView.as_view(), name="cookie_logout"),
    path("token/", CookieObtainPairView.as_view(), name="cookie_token_obtain_pair"),
    path("token/verify/", CookieTokenVerifyView.as_view(), name="cookie_token_verify"),
    path(
        "token/refresh/", CookieRefreshTokenView.as_view(), name="cookie_token_refresh"
    ),
]
