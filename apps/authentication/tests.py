import json

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.authentication import CookieJWTAuthentication


ACCESS_COOKIE = settings.SIMPLE_JWT.get("AUTH_COOKIE_NAME", "access_token")
REFRESH_COOKIE = settings.SIMPLE_JWT.get("AUTH_REFRESH_COOKIE_NAME", "refresh_token")


class CookieObtainPairViewTests(TestCase):
    """POST /api/authentication/token/ — sets access + refresh cookies on success."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="alice", password="strongpass123"
        )
        self.url = reverse("cookie_token_obtain_pair")

    def test_login_sets_both_cookies(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"username": "alice", "password": "strongpass123"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"message": "Authentication successful"})
        self.assertIn(ACCESS_COOKIE, response.cookies)
        self.assertIn(REFRESH_COOKIE, response.cookies)
        self.assertTrue(response.cookies[ACCESS_COOKIE].value)
        self.assertTrue(response.cookies[REFRESH_COOKIE].value)

    def test_login_does_not_leak_tokens_in_body(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"username": "alice", "password": "strongpass123"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_login_with_wrong_password_does_not_set_cookies(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"username": "alice", "password": "wrong"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertNotIn(ACCESS_COOKIE, response.cookies)
        self.assertNotIn(REFRESH_COOKIE, response.cookies)


class CookieRefreshTokenViewTests(TestCase):
    """POST /api/authentication/token/refresh/ — refreshes access cookie from refresh cookie."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="bob", password="pw12345678")
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.url = reverse("cookie_token_refresh")

    def test_refresh_with_valid_cookie_renews_access_cookie(self):
        self.client.cookies[REFRESH_COOKIE] = self.refresh_token

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"message": "Token refreshed successfully"})
        self.assertIn(ACCESS_COOKIE, response.cookies)
        self.assertTrue(response.cookies[ACCESS_COOKIE].value)

    def test_refresh_without_cookie_returns_401(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"error": "Refresh token is missing."})

    def test_refresh_with_invalid_cookie_returns_401(self):
        self.client.cookies[REFRESH_COOKIE] = "not.a.token"

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data, {"error": "Refresh token is invalid or expired."}
        )


class CookieTokenVerifyViewTests(TestCase):
    """POST /api/authentication/token/verify/ — verifies the access cookie."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="carol", password="pw12345678")
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.url = reverse("cookie_token_verify")

    def test_verify_with_valid_cookie_returns_200(self):
        self.client.cookies[ACCESS_COOKIE] = self.access_token

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"message": "Token is valid."})

    def test_verify_without_cookie_returns_401(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"error": "Access token is missing."})

    def test_verify_with_invalid_cookie_returns_401(self):
        self.client.cookies[ACCESS_COOKIE] = "not.a.jwt"

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data, {"error": "Access token is invalid or expired."}
        )


class CookieLogoutViewTests(TestCase):
    """POST /api/authentication/logout/ — clears cookies and blacklists the refresh token."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="dave", password="pw12345678")
        self.refresh = RefreshToken.for_user(self.user)
        self.url = reverse("cookie_logout")

    def test_logout_clears_both_cookies(self):
        self.client.cookies[ACCESS_COOKIE] = "access-value"
        self.client.cookies[REFRESH_COOKIE] = str(self.refresh)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 205)
        self.assertEqual(response.data, {"detail": "Logout successful"})
        self.assertEqual(response.cookies[ACCESS_COOKIE].value, "")
        self.assertEqual(response.cookies[REFRESH_COOKIE].value, "")

    def test_logout_blacklists_refresh_token(self):
        token_str = str(self.refresh)
        self.client.cookies[REFRESH_COOKIE] = token_str

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 205)

        refresh_url = reverse("cookie_token_refresh")
        self.client.cookies[REFRESH_COOKIE] = token_str
        replay = self.client.post(refresh_url)
        self.assertEqual(replay.status_code, 401)

    def test_logout_without_refresh_cookie_still_clears(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 205)
        self.assertEqual(response.cookies[ACCESS_COOKIE].value, "")


class CookieJWTAuthenticationTests(TestCase):
    """CookieJWTAuthentication.authenticate() — reads cookie, falls back to header, rejects malformed."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="eve", password="pw12345678")
        self.access_token = str(RefreshToken.for_user(self.user).access_token)
        self.auth = CookieJWTAuthentication()

    def test_authenticate_reads_token_from_cookie(self):
        request = self.factory.get("/")
        request.COOKIES[ACCESS_COOKIE] = self.access_token

        result = self.auth.authenticate(request)

        self.assertIsNotNone(result)
        user, _ = result
        self.assertEqual(user, self.user)

    def test_authenticate_falls_back_to_authorization_header(self):
        request = self.factory.get(
            "/", HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        result = self.auth.authenticate(request)

        self.assertIsNotNone(result)
        user, _ = result
        self.assertEqual(user, self.user)

    def test_authenticate_returns_none_when_no_credentials(self):
        request = self.factory.get("/")

        result = self.auth.authenticate(request)

        self.assertIsNone(result)

    def test_authenticate_rejects_malformed_cookie(self):
        request = self.factory.get("/")
        request.COOKIES[ACCESS_COOKIE] = "not-a-jwt-with-three-parts"

        result = self.auth.authenticate(request)

        self.assertIsNone(result)

    def test_authenticate_rejects_invalid_signature(self):
        request = self.factory.get("/")
        request.COOKIES[ACCESS_COOKIE] = "aaa.bbb.ccc"

        result = self.auth.authenticate(request)

        self.assertIsNone(result)

    def test_authenticate_rejects_empty_cookie(self):
        request = self.factory.get("/")
        request.COOKIES[ACCESS_COOKIE] = "   "

        result = self.auth.authenticate(request)

        self.assertIsNone(result)
