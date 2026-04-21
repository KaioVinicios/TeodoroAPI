from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.supply.models import Supply
from apps.supply.choices import SupplyStatus, UnitOfMeasure
from apps.supply.validators import validate_status, validate_unit_of_measure
from apps.supply.services import SupplyServices
from apps.supply_label.models import SupplyLabel
from apps.account.models import Account
from apps.account.choices import AccountType


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(username, account_type=AccountType.ADMIN, cpf="529.982.247-25"):
    user = User.objects.create_user(
        username=username,
        password="StrongPass!23",
        email=f"{username}@test.com",
        first_name="Test",
        last_name="User",
    )
    Account.objects.create(
        user=user,
        account_type=account_type,
        cpf=cpf,
        address="Rua das Flores, 10",
        phone_number="(79) 91234-5678",
    )
    return user


def auth_header(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def make_label(**kwargs):
    defaults = {
        "name": "Amoxicilina",
        "category": "Antibiótico",
    }
    defaults.update(kwargs)
    return SupplyLabel.objects.create(**defaults)


def make_supply(label=None, **kwargs):
    if label is None:
        label = make_label()
    defaults = {
        "supply_label": label,
        "status": SupplyStatus.AVAILABLE,
        "description": "Estoque principal",
        "unit_of_measure": UnitOfMeasure.UNIT,
    }
    defaults.update(kwargs)
    return Supply.objects.create(**defaults)


# ── Validator tests ───────────────────────────────────────────────────────────

class ValidatorTests(TestCase):

    def test_validate_status_valid(self):
        for s in SupplyStatus.values:
            validate_status(s)  # should not raise

    def test_validate_status_invalid_raises(self):
        with self.assertRaises(ValidationError):
            validate_status("invalid_status")

    def test_validate_unit_of_measure_valid(self):
        for u in UnitOfMeasure.values:
            validate_unit_of_measure(u)  # should not raise

    def test_validate_unit_of_measure_invalid_raises(self):
        with self.assertRaises(ValidationError):
            validate_unit_of_measure("invalid_unit")


# ── Model tests ───────────────────────────────────────────────────────────────

class SupplyModelTests(TestCase):

    def test_create_supply(self):
        supply = make_supply()
        self.assertEqual(supply.status, SupplyStatus.AVAILABLE)
        self.assertEqual(supply.unit_of_measure, UnitOfMeasure.UNIT)

    def test_str_representation(self):
        supply = make_supply()
        self.assertIn("Amoxicilina", str(supply))

    def test_status_defaults_to_available(self):
        label = make_label()
        supply = Supply.objects.create(
            supply_label=label,
            description="Teste",
            unit_of_measure=UnitOfMeasure.GRAM,
        )
        self.assertEqual(supply.status, SupplyStatus.AVAILABLE)

    def test_supply_label_protect_on_delete(self):
        """Deleting a label that has supplies should raise ProtectedError."""
        from django.db.models import ProtectedError
        supply = make_supply()
        with self.assertRaises(ProtectedError):
            supply.supply_label.delete()


# ── Service tests ─────────────────────────────────────────────────────────────

class SupplyServiceTests(TestCase):

    def setUp(self):
        self.label = make_label()

    def test_list_all_returns_all_supplies(self):
        make_supply(self.label)
        make_supply(self.label, status=SupplyStatus.DEPLETED)
        self.assertEqual(SupplyServices.list_all().count(), 2)

    def test_get_existing_supply(self):
        supply = make_supply(self.label)
        fetched = SupplyServices.get(supply.pk)
        self.assertEqual(fetched.pk, supply.pk)

    def test_get_nonexistent_raises_404(self):
        from django.http import Http404
        with self.assertRaises(Http404):
            SupplyServices.get(9999)

    def test_create_supply(self):
        data = {
            "supply_label": self.label,
            "status": SupplyStatus.AVAILABLE,
            "description": "Lote novo",
            "unit_of_measure": UnitOfMeasure.MILLILITER,
        }
        supply = SupplyServices.create(data)
        self.assertEqual(supply.unit_of_measure, UnitOfMeasure.MILLILITER)
        self.assertTrue(Supply.objects.filter(pk=supply.pk).exists())

    def test_update_supply_status(self):
        supply = make_supply(self.label)
        updated = SupplyServices.update(supply, {"status": SupplyStatus.DEPLETED})
        self.assertEqual(updated.status, SupplyStatus.DEPLETED)

    def test_update_supply_unit_of_measure(self):
        supply = make_supply(self.label)
        updated = SupplyServices.update(supply, {"unit_of_measure": UnitOfMeasure.KILOGRAM})
        self.assertEqual(updated.unit_of_measure, UnitOfMeasure.KILOGRAM)

    def test_delete_supply(self):
        supply = make_supply(self.label)
        pk = supply.pk
        SupplyServices.delete(pk)
        self.assertFalse(Supply.objects.filter(pk=pk).exists())

    def test_delete_nonexistent_supply_raises_404(self):
        from django.http import Http404
        with self.assertRaises(Http404):
            SupplyServices.delete(9999)

    def test_list_all_uses_select_related(self):
        """Ensures supply_label is prefetched (no extra queries)."""
        make_supply(self.label)
        qs = SupplyServices.list_all()
        with self.assertNumQueries(0):
            _ = qs[0].supply_label.name


# ── Supply API tests ──────────────────────────────────────────────────────────

class SupplyListAPIViewTests(APITestCase):

    def setUp(self):
        self.admin = make_user("admin_user", AccountType.ADMIN, "529.982.247-25")
        self.customer = make_user("customer_user", AccountType.CUSTOMER, "153.509.460-56")
        self.label = make_label()
        self.url = reverse("supply:supply_list")

    def _valid_payload(self):
        return {
            "supply_label": self.label.pk,
            "status": SupplyStatus.AVAILABLE,
            "description": "Estoque A",
            "unit_of_measure": UnitOfMeasure.UNIT,
        }

    # GET -- list
    def test_list_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_authenticated_returns_200(self):
        response = self.client.get(self.url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)

    def test_list_returns_correct_count(self):
        make_supply(self.label)
        make_supply(self.label, status=SupplyStatus.RESERVED)
        response = self.client.get(self.url, **auth_header(self.admin))
        self.assertEqual(len(response.data["data"]), 2)

    def test_customer_can_list_supplies(self):
        response = self.client.get(self.url, **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_includes_supply_label_detail(self):
        make_supply(self.label)
        response = self.client.get(self.url, **auth_header(self.admin))
        item = response.data["data"][0]
        self.assertIn("supply_label_detail", item)
        self.assertEqual(item["supply_label_detail"]["name"], self.label.name)

    # POST -- create
    def test_create_unauthenticated_returns_401(self):
        response = self.client.post(self.url, self._valid_payload())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_create_supply_returns_403(self):
        response = self.client.post(self.url, self._valid_payload(), **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_supply_returns_201(self):
        response = self.client.post(self.url, self._valid_payload(), **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["status"], SupplyStatus.AVAILABLE)

    def test_create_with_invalid_status_returns_400(self):
        payload = self._valid_payload()
        payload["status"] = "invalid"
        response = self.client.post(self.url, payload, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_invalid_unit_of_measure_returns_400(self):
        payload = self._valid_payload()
        payload["unit_of_measure"] = "invalid"
        response = self.client.post(self.url, payload, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_nonexistent_label_returns_400(self):
        payload = self._valid_payload()
        payload["supply_label"] = 9999
        response = self.client.post(self.url, payload, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_missing_required_fields_returns_400(self):
        response = self.client.post(self.url, {}, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SupplyDetailAPIViewTests(APITestCase):

    def setUp(self):
        self.admin = make_user("admin_user", AccountType.ADMIN, "529.982.247-25")
        self.customer = make_user("customer_user", AccountType.CUSTOMER, "153.509.460-56")
        self.label = make_label()
        self.supply = make_supply(self.label)
        self.url = reverse("supply:supply_detail", kwargs={"pk": self.supply.pk})
        self.not_found_url = reverse("supply:supply_detail", kwargs={"pk": 9999})

    # GET -- retrieve
    def test_retrieve_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_existing_supply_returns_200(self):
        response = self.client.get(self.url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], self.supply.status)

    def test_retrieve_nonexistent_returns_404(self):
        response = self.client.get(self.not_found_url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_can_retrieve_supply(self):
        response = self.client.get(self.url, **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_response_has_supply_label_detail(self):
        response = self.client.get(self.url, **auth_header(self.admin))
        self.assertIn("supply_label_detail", response.data["data"])

    # PATCH -- partial update
    def test_patch_unauthenticated_returns_401(self):
        response = self.client.patch(self.url, {"status": SupplyStatus.RESERVED})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_patch_returns_403(self):
        response = self.client.patch(
            self.url, {"status": SupplyStatus.RESERVED}, **auth_header(self.customer)
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_patch_status(self):
        response = self.client.patch(
            self.url, {"status": SupplyStatus.DEPLETED}, **auth_header(self.admin)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], SupplyStatus.DEPLETED)

    def test_admin_can_patch_unit_of_measure(self):
        response = self.client.patch(
            self.url, {"unit_of_measure": UnitOfMeasure.LITER}, **auth_header(self.admin)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["unit_of_measure"], UnitOfMeasure.LITER)

    def test_patch_with_invalid_status_returns_400(self):
        response = self.client.patch(self.url, {"status": "invalid"}, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_nonexistent_returns_404(self):
        response = self.client.patch(
            self.not_found_url, {"status": SupplyStatus.RESERVED}, **auth_header(self.admin)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # DELETE -- destroy
    def test_delete_unauthenticated_returns_401(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_delete_returns_403(self):
        response = self.client.delete(self.url, **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_supply_returns_204(self):
        response = self.client.delete(self.url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Supply.objects.filter(pk=self.supply.pk).exists())

    def test_delete_nonexistent_returns_404(self):
        response = self.client.delete(self.not_found_url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)