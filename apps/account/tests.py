from apps.account.models import Account
from rest_framework.test import APIClient
from django.test import TestCase, RequestFactory
from apps.account.services import AccountServices
from apps.account.permissions import IsNotCustomer
from apps.account.serializers import AccountSerializer
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ValidationError as DjangoValidationError


class IsNotCustomerPermissionTests(TestCase):
    """
    Tests for the ``IsNotCustomer`` DRF permission class.

    The permission must grant access to every authenticated user whose
    linked ``Account`` is **not** of type ``customer`` and deny everyone
    else (customers, anonymous users, and users without an ``Account``).
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsNotCustomer()

    def _make_user_with_account(self, username, account_type):
        user = User.objects.create_user(username=username, password="pw12345!")
        Account.objects.create(
            user=user,
            account_type=account_type,
            cpf=self._valid_cpf_for(username),
            address="Rua X, 1",
            phone_number="(11) 91234-5678",
        )
        return user

    @staticmethod
    def _valid_cpf_for(seed):
        cpf_map = {
            "adminuser": "529.982.247-25",
            "customeruser": "111.444.777-35",
        }
        return cpf_map[seed]

    def test_denies_customer(self):
        """A user whose account_type is ``customer`` must be denied."""
        user = self._make_user_with_account("customeruser", "customer")
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, view=None))

    def test_allows_non_customer(self):
        """A user with any non-customer account_type (e.g. ``admin``) must be allowed."""
        user = self._make_user_with_account("adminuser", "admin")
        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, view=None))

    def test_denies_anonymous(self):
        """Anonymous (unauthenticated) requests must be denied."""
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, view=None))

    def test_denies_user_without_account(self):
        """
        Authenticated users that do not have a related ``Account`` row
        must be denied instead of raising ``Account.DoesNotExist``.
        """
        user = User.objects.create_user(username="orphan", password="pw12345!")
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, view=None))


class AccountSerializerTests(TestCase):
    """
    Tests for ``AccountSerializer``.

    The serializer exposes a *flat* representation that mixes ``User``
    and ``Account`` fields in a single JSON object and is responsible
    for validating business rules such as CPF format, account_type
    choices and required fields. Password handling (hashing, not
    echoing it back) is covered here as well.
    """

    def _valid_payload(self, **overrides):
        payload = {
            "username": "joao",
            "password": "StrongPass!23",
            "email": "joao@example.com",
            "first_name": "Joao",
            "last_name": "Silva",
            "account_type": "customer",
            "cpf": "529.982.247-25",
            "address": "Rua das Flores, 10",
            "phone_number": "(11) 91234-5678",
            "organization": None,
        }
        payload.update(overrides)
        return payload

    def test_valid_payload_is_valid(self):
        """A fully-populated, well-formed payload must pass validation."""
        serializer = AccountSerializer(data=self._valid_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_username_is_invalid(self):
        """``username`` is required and its absence must be reported as an error."""
        payload = self._valid_payload()
        payload.pop("username")
        serializer = AccountSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)

    def test_invalid_account_type_is_invalid(self):
        """``account_type`` must be one of the declared choices (e.g. ``customer``/``admin``)."""
        serializer = AccountSerializer(data=self._valid_payload(account_type="pirate"))
        self.assertFalse(serializer.is_valid())
        self.assertIn("account_type", serializer.errors)

    def test_invalid_cpf_is_invalid(self):
        """
        CPFs with invalid check digits (e.g. ``000.000.000-00``) must be
        rejected by the custom CPF validator.
        """
        serializer = AccountSerializer(data=self._valid_payload(cpf="000.000.000-00"))
        self.assertFalse(serializer.is_valid())
        self.assertIn("cpf", serializer.errors)

    def test_to_representation_is_flat_and_omits_password(self):
        """
        Output must be a flat object (no nested ``user`` key) and must
        never leak the password — hashed or plain — back to the client.
        """
        user = User.objects.create_user(
            username="maria",
            password="StrongPass!23",
            email="maria@example.com",
            first_name="Maria",
            last_name="Souza",
        )
        account = Account.objects.create(
            user=user,
            account_type="admin",
            cpf="529.982.247-25",
            address="Av. Brasil, 99",
            phone_number="(11) 91234-5678",
        )
        data = AccountSerializer(account).data
        self.assertEqual(data["username"], "maria")
        self.assertEqual(data["email"], "maria@example.com")
        self.assertEqual(data["first_name"], "Maria")
        self.assertEqual(data["last_name"], "Souza")
        self.assertEqual(data["account_type"], "admin")
        self.assertEqual(data["cpf"], "529.982.247-25")
        self.assertNotIn("password", data)
        self.assertNotIn("user", data)


class AccountServicesTests(TestCase):
    """
    Tests for ``AccountServices`` — the service layer that orchestrates
    ``User`` + ``Account`` persistence.

    These tests focus on transactional behavior (atomic create), password
    hashing, partial updates across both models and hard-delete semantics.
    They bypass HTTP and DRF and call the services directly so failures
    here point squarely at the service layer.
    """

    def _valid_data(self, **overrides):
        data = {
            "user": {
                "username": "joao",
                "password": "StrongPass!23",
                "email": "joao@example.com",
                "first_name": "Joao",
                "last_name": "Silva",
            },
            "account_type": "customer",
            "cpf": "529.982.247-25",
            "address": "Rua das Flores, 10",
            "phone_number": "(11) 91234-5678",
            "organization": None,
        }
        data.update(overrides)
        return data

    def test_create_persists_user_and_account(self):
        """``create`` must persist exactly one ``User`` and one ``Account`` row linked to it."""
        account = AccountServices.create(self._valid_data())
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(account.user.username, "joao")
        self.assertEqual(account.account_type, "customer")

    def test_create_hashes_password(self):
        """
        The service must hash the incoming plaintext password —
        ``User.password`` must differ from the input and ``check_password``
        must succeed against the original value.
        """
        account = AccountServices.create(self._valid_data())
        self.assertTrue(account.user.check_password("StrongPass!23"))
        self.assertNotEqual(account.user.password, "StrongPass!23")

    def test_create_rolls_back_user_if_account_fails(self):
        """
        If ``Account`` creation fails validation (invalid CPF) after the
        ``User`` was already inserted, the whole operation must be rolled
        back so we don't leak orphan ``User`` rows.
        """
        bad_data = self._valid_data(cpf="000.000.000-00")
        with self.assertRaises(DjangoValidationError):
            AccountServices.create(bad_data)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Account.objects.count(), 0)

    def test_update_changes_user_and_account_fields(self):
        """
        ``update`` must support partial updates that span both models
        in a single call (``User.first_name`` + ``Account.address``).
        """
        account = AccountServices.create(self._valid_data())
        updated = AccountServices.update(
            account,
            {"user": {"first_name": "Novo"}, "address": "Rua Nova, 42"},
        )
        updated.refresh_from_db()
        self.assertEqual(updated.user.first_name, "Novo")
        self.assertEqual(updated.address, "Rua Nova, 42")

    def test_update_password_rehashes(self):
        """
        Updating ``user.password`` must go through ``set_password`` so
        the new value is stored hashed, not as plaintext.
        """
        account = AccountServices.create(self._valid_data())
        AccountServices.update(account, {"user": {"password": "NewPass!234"}})
        account.user.refresh_from_db()
        self.assertTrue(account.user.check_password("NewPass!234"))

    def test_delete_removes_user_and_account(self):
        """``delete`` must cascade and remove both the ``Account`` and its ``User``."""
        account = AccountServices.create(self._valid_data())
        AccountServices.delete(account.pk)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Account.objects.count(), 0)

    def test_list_all_returns_queryset(self):
        """``list_all`` must return every persisted ``Account`` (sanity-check on the queryset)."""
        AccountServices.create(self._valid_data())
        second = self._valid_data(cpf="111.444.777-35")
        second["user"] = {
            "username": "maria",
            "password": "StrongPass!23",
            "email": "maria@example.com",
            "first_name": "Maria",
            "last_name": "Souza",
        }
        AccountServices.create(second)
        self.assertEqual(AccountServices.list_all().count(), 2)


class AccountCreateAPITests(TestCase):
    """
    HTTP-level tests for ``POST /api/accounts/`` (account signup).

    Account creation is the only endpoint in this resource that is
    intentionally open to unauthenticated clients, so these tests pin
    that contract and the envelope shape (``response.data["data"]``).
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/accounts/"

    def _valid_payload(self, **overrides):
        payload = {
            "username": "joao",
            "password": "StrongPass!23",
            "email": "joao@example.com",
            "first_name": "Joao",
            "last_name": "Silva",
            "account_type": "customer",
            "cpf": "529.982.247-25",
            "address": "Rua das Flores, 10",
            "phone_number": "(11) 91234-5678",
            "organization": None,
        }
        payload.update(overrides)
        return payload

    def test_post_creates_user_and_account_without_auth(self):
        """
        Anonymous clients must be able to sign up: the endpoint returns
        201, persists both rows, echoes the created resource under
        ``data`` and never leaks the password.
        """
        response = self.client.post(self.url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(response.data["data"]["username"], "joao")
        self.assertNotIn("password", response.data["data"])

    def test_post_with_invalid_cpf_returns_400(self):
        """Invalid payloads surface as 400 with per-field errors (here ``cpf``)."""
        response = self.client.post(
            self.url,
            self._valid_payload(cpf="000.000.000-00"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("cpf", response.data)


class AccountListAPITests(TestCase):
    """
    HTTP-level tests for ``GET /api/accounts/`` (account listing).

    Listing is a privileged operation: anonymous users get 401,
    customers are explicitly forbidden (403) via ``IsNotCustomer`` and
    admins receive the full collection wrapped in the ``data`` envelope.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/accounts/"
        self.customer = self._make_account("customeruser", "customer", "111.444.777-35")
        self.admin = self._make_account("adminuser", "admin", "529.982.247-25")

    def _make_account(self, username, account_type, cpf):
        user = User.objects.create_user(
            username=username, password="Pw12345!", email=f"{username}@example.com"
        )
        return Account.objects.create(
            user=user,
            account_type=account_type,
            cpf=cpf,
            address="Rua X, 1",
            phone_number="(11) 91234-5678",
        )

    def test_list_requires_authentication(self):
        """Unauthenticated requests must get 401, not 403 or 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_list_forbidden_for_customer(self):
        """Authenticated customers are not allowed to browse other accounts."""
        self.client.force_authenticate(self.customer.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_list_allowed_for_admin(self):
        """Admins see every account in the system under the ``data`` key."""
        self.client.force_authenticate(self.admin.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 2)


class AccountDetailAPITests(TestCase):
    """
    HTTP-level tests for ``/api/accounts/<pk>/`` (retrieve/update/delete).

    Covers authorization (auth required, customer vs. admin differences),
    the flat response shape, partial updates that cross model boundaries
    and the hard-delete cascade to the underlying ``User``.
    """

    def setUp(self):
        self.client = APIClient()
        self.customer = self._make_account("customeruser", "customer", "111.444.777-35")
        self.admin = self._make_account("adminuser", "admin", "529.982.247-25")
        self.url = f"/api/accounts/{self.customer.pk}/"

    def _make_account(self, username, account_type, cpf):
        user = User.objects.create_user(
            username=username, password="Pw12345!", email=f"{username}@example.com"
        )
        return Account.objects.create(
            user=user,
            account_type=account_type,
            cpf=cpf,
            address="Rua X, 1",
            phone_number="(11) 91234-5678",
        )

    def test_retrieve_requires_authentication(self):
        """GET on a detail URL must require authentication (401 for anon)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_retrieve_returns_flat_shape(self):
        """
        The retrieved payload must expose a flat shape (``username`` at
        the top level, no nested ``user`` object) consistent with the
        serializer contract.
        """
        self.client.force_authenticate(self.customer.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["username"], "customeruser")
        self.assertEqual(data["account_type"], "customer")
        self.assertNotIn("user", data)

    def test_retrieve_not_found(self):
        """Unknown primary keys return 404, not 500 or an empty body."""
        self.client.force_authenticate(self.customer.user)
        response = self.client.get("/api/accounts/9999/")
        self.assertEqual(response.status_code, 404)

    def test_patch_updates_user_and_account_fields(self):
        """
        PATCH must be able to update fields on both ``User`` (first_name)
        and ``Account`` (address) in a single request, mirroring the
        service-layer behavior.
        """
        self.client.force_authenticate(self.customer.user)
        response = self.client.patch(
            self.url,
            {"first_name": "Novo", "address": "Rua Nova, 42"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.customer.refresh_from_db()
        self.customer.user.refresh_from_db()
        self.assertEqual(self.customer.user.first_name, "Novo")
        self.assertEqual(self.customer.address, "Rua Nova, 42")

    def test_delete_forbidden_for_customer(self):
        """Customers cannot delete accounts (even, for now, their own)."""
        self.client.force_authenticate(self.customer.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_delete_allowed_for_admin(self):
        """
        Admins can delete any account; the operation must return 204 and
        cascade to remove the linked ``User`` so no orphan rows remain.
        """
        self.client.force_authenticate(self.admin.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Account.objects.filter(pk=self.customer.pk).exists())
        self.assertFalse(User.objects.filter(pk=self.customer.user_id).exists())
