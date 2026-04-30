import logging
from datetime import timedelta
from django.conf import settings
from rest_framework import permissions, serializers
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
    OpenApiResponse,
)


LogoutResponseSerializer = inline_serializer(
    name="LogoutResponse",
    fields={"detail": serializers.CharField()},
)

logger = logging.getLogger(__name__)


class CookieObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code != status.HTTP_200_OK:
            return response

        try:
            if not hasattr(response, "data") or not isinstance(response.data, dict):
                logger.error("Invalid response data format from TokenObtainPairView")
                return Response(
                    {"error": "Authentication failed. Invalid response format."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            access = response.data.get("access")
            refresh = response.data.get("refresh")

            if not access or not refresh:
                logger.error("Missing tokens in authentication response")
                return Response(
                    {"error": "Authentication failed. Tokens not generated."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            try:
                jwt = settings.SIMPLE_JWT

                cookie_http_only = jwt.get("AUTH_COOKIE_HTTP_ONLY", True)
                cookie_secure = jwt.get("AUTH_COOKIE_SECURE", False)
                cookie_samesite = jwt.get("AUTH_COOKIE_SAMESITE", "Lax")
                cookie_path = jwt.get("AUTH_COOKIE_PATH", "/")

                response.set_cookie(
                    key=jwt.get("AUTH_COOKIE_NAME", "access_token"),
                    value=access,
                    max_age=int(
                        jwt.get(
                            "ACCESS_TOKEN_LIFETIME", timedelta(hours=1)
                        ).total_seconds()
                    ),
                    httponly=cookie_http_only,
                    secure=cookie_secure,
                    samesite=cookie_samesite,
                    path=cookie_path,
                )

                response.set_cookie(
                    key=jwt.get("AUTH_REFRESH_COOKIE_NAME", "refresh_token"),
                    value=refresh,
                    max_age=int(
                        jwt.get(
                            "REFRESH_TOKEN_LIFETIME", timedelta(days=3)
                        ).total_seconds()
                    ),
                    httponly=cookie_http_only,
                    secure=cookie_secure,
                    samesite=cookie_samesite,
                    path=cookie_path,
                )

                response.data = {"message": "Authentication successful"}

            except Exception as e:
                logger.error(f"Error setting cookies: {str(e)}")
                return Response(
                    {"error": "Authentication successful but failed to set cookies."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return response

        except Exception as e:
            logger.error(f"Unexpected error in CookieObtainPairView: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred during authentication."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CookieRefreshTokenView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        jwt_settings = getattr(settings, "SIMPLE_JWT", {})
        refresh_cookie_name = jwt_settings.get(
            "AUTH_REFRESH_COOKIE_NAME", "refresh_token"
        )

        refresh_token = request.COOKIES.get(refresh_cookie_name)

        if not refresh_token:
            logger.warning("Refresh token not provided.")
            return Response(
                {"error": "Refresh token is missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)  # Create new access token here
        except TokenError as error:
            logger.warning(f"Invalid refresh token: {error}")
            return Response(
                {"error": "Refresh token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = serializer.validated_data
        access = tokens.get("access")
        new_refresh = tokens.get("refresh") or refresh_token

        if not access:
            logger.error("Refresh endpoint did not return an access token.")
            return Response(
                {"error": "Failed to refresh access token."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = Response(
            {"message": "Token refreshed successfully"}, status=status.HTTP_200_OK
        )

        try:
            cookie_http_only = jwt_settings.get("AUTH_COOKIE_HTTP_ONLY", True)
            cookie_secure = jwt_settings.get("AUTH_COOKIE_SECURE", False)
            cookie_samesite = jwt_settings.get("AUTH_COOKIE_SAMESITE", "Lax")
            cookie_path = jwt_settings.get("AUTH_COOKIE_PATH", "/")

            response.set_cookie(
                key=jwt_settings.get("AUTH_COOKIE_NAME", "access_token"),
                value=access,
                max_age=int(
                    jwt_settings.get(
                        "ACCESS_TOKEN_LIFETIME", timedelta(hours=1)
                    ).total_seconds()
                ),
                httponly=cookie_http_only,
                secure=cookie_secure,
                samesite=cookie_samesite,
                path=cookie_path,
            )

            response.set_cookie(
                key=refresh_cookie_name,
                value=new_refresh,
                max_age=int(
                    jwt_settings.get(
                        "REFRESH_TOKEN_LIFETIME", timedelta(days=3)
                    ).total_seconds()
                ),
                httponly=cookie_http_only,
                secure=cookie_secure,
                samesite=cookie_samesite,
                path=cookie_path,
            )

        except Exception as error:
            logger.error(f"Error setting refresh cookies: {error}")
            return Response(
                {"error": "Tokens refreshed but failed to set cookies."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return response


class CookieTokenVerifyView(TokenVerifyView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        jwt_settings = getattr(settings, "SIMPLE_JWT", {})
        access_cookie_name = jwt_settings.get("AUTH_COOKIE_NAME", "access_token")

        token = request.COOKIES.get(access_cookie_name)

        if not token:
            logger.warning("Token verification requested without token.")
            return Response(
                {"error": "Access token is missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenVerifySerializer(data={"token": token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as error:
            logger.warning(f"Invalid access token: {error}")
            return Response(
                {"error": "Access token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response({"message": "Token is valid."}, status=status.HTTP_200_OK)


@extend_schema(tags=["authentication"])
@extend_schema_view(
    post=extend_schema(
        operation_id="auth_logout",
        summary="Logout",
        description=(
            "Blacklists the refresh token (if present) and clears the access "
            "and refresh cookies."
        ),
        request=None,
        responses={
            205: LogoutResponseSerializer,
        },
    ),
)
class CookieLogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LogoutResponseSerializer

    def post(self, request):
        jwt_settings = getattr(settings, "SIMPLE_JWT", {})
        refresh_cookie_name = jwt_settings.get(
            "AUTH_REFRESH_COOKIE_NAME", "refresh_token"
        )
        refresh_token = request.COOKIES.get(refresh_cookie_name)

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass  # Need to handle this exception in a better way.

        response = Response(
            {"detail": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT
        )

        response.delete_cookie(
            key=jwt_settings.get("AUTH_COOKIE_NAME", "access_token"),
            path="/",
            samesite=jwt_settings.get("AUTH_COOKIE_SAMESITE", "None"),
        )

        response.delete_cookie(
            key=jwt_settings.get("AUTH_REFRESH_COOKIE_NAME", "refresh_token"),
            path="/",
            samesite=jwt_settings.get("AUTH_COOKIE_SAMESITE", "None"),
        )

        return response
