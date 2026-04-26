from apps.account.models import Account
from apps.inspection.models import Inspection
from apps.inspection.services import InspectionServices
from apps.inspection.serializers import InspectionSerializer
from django.contrib.auth.models import User
from django.http import Http404
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
import datetime

# ──────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ──────────────────────────────────────────────────────────────────────────────


def _make_account(username, account_type, cpf):
    """Create a User + Account pair in one call."""
    user = User.objects.create_user(
        username=username,
        password="Pw12345!",
        email=f"{username}@example.com",
    )
    Account.objects.create(
        user=user,
        account_type=account_type,
        cpf=cpf,
        address="Rua X, 1",
        phone_number="(11) 91234-5678",
    )
    return user


# ──────────────────────────────────────────────────────────────────────────────
# Serializer
# ──────────────────────────────────────────────────────────────────────────────


class InspectionSerializerTests(TestCase):
    """
    Tests for ``InspectionSerializer``.

    The serializer accepts a ``responsible`` FK (user PK), validates that the
    referenced user is an auditor, and exposes ``is_complete`` and
    ``completion_date`` on output.  These tests verify valid payloads, invalid
    FK references and that a non-auditor responsible triggers a validation error.
    """

    def setUp(self):
        self.auditor = _make_account("auditor1", "auditor", "529.982.247-25")
        self.customer = _make_account("customer1", "customer", "111.444.777-35")

    def test_valid_payload_is_valid(self):
        """A payload whose responsible is an auditor must pass validation."""
        serializer = InspectionSerializer(data={"responsible": self.auditor.pk})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_non_auditor_responsible_is_invalid(self):
        """
        Assigning a non-auditor user as responsible must be rejected by
        ``validate_responsible_is_auditor``.
        """
        serializer = InspectionSerializer(data={"responsible": self.customer.pk})
        self.assertFalse(serializer.is_valid())
        self.assertIn("responsible", serializer.errors)

    def test_nonexistent_responsible_is_invalid(self):
        """A responsible PK that does not exist must yield a validation error."""
        serializer = InspectionSerializer(data={"responsible": 9999})
        self.assertFalse(serializer.is_valid())
        self.assertIn("responsible", serializer.errors)

    def test_to_representation_exposes_expected_fields(self):
        """
        Output must include ``is_complete``, ``completion_date``, and
        ``responsible`` without raising and without any unexpected nesting.
        """
        inspection = Inspection.objects.create(
            responsible=self.auditor,
            is_complete=False,
            completion_date=None,
        )
        data = InspectionSerializer(inspection).data
        self.assertIn("is_complete", data)
        self.assertIn("completion_date", data)
        self.assertIn("responsible", data)
        self.assertFalse(data["is_complete"])
        self.assertIsNone(data["completion_date"])


# ──────────────────────────────────────────────────────────────────────────────
# Service layer
# ──────────────────────────────────────────────────────────────────────────────


class InspectionServicesTests(TestCase):
    """
    Tests for ``InspectionServices``.

    Exercises persistence, the forced-incomplete invariant on creation, the
    guard against updating completed inspections, and hard-delete semantics.
    All tests bypass HTTP and call the service directly so failures point
    squarely at the service layer.
    """

    def setUp(self):
        self.auditor = _make_account("auditor1", "auditor", "529.982.247-25")

    def _create(self, **overrides):
        data = {"responsible": self.auditor}
        data.update(overrides)
        return InspectionServices.create(data)

    # -- create ----------------------------------------------------------------

    def test_create_persists_inspection(self):
        """``create`` must persist exactly one ``Inspection`` row."""
        inspection = self._create()
        self.assertEqual(Inspection.objects.count(), 1)
        self.assertEqual(inspection.responsible, self.auditor)

    def test_create_forces_is_complete_false(self):
        """
        Even when the caller passes ``is_complete=True``, the service must
        override it to ``False`` so an inspection always starts as pending.
        """
        inspection = self._create(is_complete=True)
        self.assertFalse(inspection.is_complete)

    def test_create_forces_completion_date_none(self):
        """
        Likewise, any supplied ``completion_date`` must be discarded on
        creation and stored as ``None``.
        """
        inspection = self._create(completion_date=datetime.date.today())
        self.assertIsNone(inspection.completion_date)

    # -- update ----------------------------------------------------------------

    def test_update_changes_responsible(self):
        """``update`` must persist changes to the ``responsible`` field."""
        auditor2 = _make_account("auditor2", "auditor", "111.444.777-35")
        inspection = self._create()
        updated = InspectionServices.update(inspection, {"responsible": auditor2})
        updated.refresh_from_db()
        self.assertEqual(updated.responsible, auditor2)

    def test_update_raises_if_already_complete(self):
        """
        Calling ``update`` on an inspection whose ``is_complete`` flag is
        already ``True`` must raise ``ValidationError`` without mutating the row.
        """
        inspection = self._create()
        inspection.is_complete = True
        inspection.save()
        with self.assertRaises(ValidationError):
            InspectionServices.update(inspection, {"responsible": self.auditor})

    # -- delete ----------------------------------------------------------------

    def test_delete_removes_inspection(self):
        """``delete`` must hard-delete the ``Inspection`` row."""
        inspection = self._create()
        InspectionServices.delete(inspection.pk)
        self.assertEqual(Inspection.objects.count(), 0)

    def test_delete_unknown_pk_raises_404(self):
        """Deleting a non-existent PK must raise ``Http404``."""
        with self.assertRaises(Http404):
            InspectionServices.delete(9999)

    # -- get -------------------------------------------------------------------

    def test_get_returns_inspection(self):
        """``get`` must return the correct ``Inspection`` by PK."""
        inspection = self._create()
        fetched = InspectionServices.get(inspection.pk)
        self.assertEqual(fetched.pk, inspection.pk)

    def test_get_unknown_pk_raises_404(self):
        """``get`` on a non-existent PK must raise ``Http404``."""
        with self.assertRaises(Http404):
            InspectionServices.get(9999)

    # -- list_all --------------------------------------------------------------

    def test_list_all_returns_all_inspections(self):
        """``list_all`` must return a queryset containing every persisted row."""
        auditor2 = _make_account("auditor2", "auditor", "111.444.777-35")
        self._create()
        InspectionServices.create({"responsible": auditor2})
        self.assertEqual(InspectionServices.list_all().count(), 2)


# ──────────────────────────────────────────────────────────────────────────────
# List endpoint  GET / POST  /api/inspections/
# ──────────────────────────────────────────────────────────────────────────────


class InspectionListAPITests(TestCase):
    """
    HTTP-level tests for ``GET /api/inspections/`` and
    ``POST /api/inspections/``.

    Gets must be allowed for any authenticated user and return 200 with
    the collection wrapped under the ``data`` key.  Posts must create a new
    inspection and return 201 with the created resource under ``data``.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/inspections/"
        self.auditor = _make_account("auditor1", "auditor", "529.982.247-25")
        self.customer = _make_account("customer1", "customer", "111.444.777-35")

    # -- GET -------------------------------------------------------------------

    def test_list_requires_authentication(self):
        """Anonymous requests must receive 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_list_for_non_auditor(self):
        """Authenticated customers must receive 200."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_allowed_for_auditor(self):
        """
        Auditors may list inspections; the response must be 200 and wrap
        the collection under the ``data`` key.
        """
        Inspection.objects.create(responsible=self.auditor, is_complete=False)
        self.client.force_authenticate(self.auditor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)
        self.assertEqual(len(response.data["data"]), 1)

    def test_list_returns_empty_data_when_no_inspections(self):
        """An empty table must yield 200 with ``data`` as an empty list."""
        self.client.force_authenticate(self.auditor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])

    # -- POST ------------------------------------------------------------------

    def test_post_requires_authentication(self):
        """Anonymous POST must receive 401."""
        response = self.client.post(
            self.url, {"responsible": self.auditor.pk}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_post_forbidden_for_customer(self):
        """Customer POST must receive 403."""
        self.client.force_authenticate(self.customer)
        response = self.client.post(
            self.url, {"responsible": self.auditor.pk}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_post_creates_inspection_for_auditor(self):
        """
        An auditor posting a valid payload must receive 201, persist one row,
        and get the created resource back under the ``data`` key.
        """
        self.client.force_authenticate(self.auditor)
        response = self.client.post(
            self.url, {"responsible": self.auditor.pk}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Inspection.objects.count(), 1)
        self.assertIn("data", response.data)

    def test_post_with_non_auditor_responsible_returns_400(self):
        """Assigning a non-auditor as responsible must surface as 400."""
        self.client.force_authenticate(self.auditor)
        response = self.client.post(
            self.url, {"responsible": self.customer.pk}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_post_created_inspection_is_never_complete(self):
        """
        The service must force ``is_complete=False`` regardless of the
        payload; the created resource must reflect this invariant.
        """
        self.client.force_authenticate(self.auditor)
        response = self.client.post(
            self.url,
            {"responsible": self.auditor.pk, "is_complete": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertFalse(response.data["data"]["is_complete"])


# ──────────────────────────────────────────────────────────────────────────────
# Detail endpoint  GET / PATCH / DELETE  /api/inspections/<pk>/
# ──────────────────────────────────────────────────────────────────────────────


class InspectionDetailAPITests(TestCase):
    """
    HTTP-level tests for ``/api/inspections/<pk>/``.

    Covers authentication guards, 404 handling, partial updates (including the
    completed-inspection guard), and hard-delete behaviour.
    """

    def setUp(self):
        self.client = APIClient()
        self.auditor = _make_account("auditor1", "auditor", "529.982.247-25")
        self.customer = _make_account("customer1", "customer", "111.444.777-35")
        self.inspection = Inspection.objects.create(
            responsible=self.auditor, is_complete=False
        )
        self.url = f"/api/inspections/{self.inspection.pk}/"

    # -- GET -------------------------------------------------------------------

    def test_retrieve_requires_authentication(self):
        """Anonymous GET must receive 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_retrieve_for_non_auditor(self):
        """Customer GET must receive 200."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_returns_inspection_for_auditor(self):
        """
        An auditor fetching an existing inspection must get 200 with the
        resource nested under the ``data`` key.
        """
        self.client.force_authenticate(self.auditor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"]["responsible"], self.auditor.pk)

    def test_retrieve_not_found(self):
        """A request for an unknown PK must return 404."""
        self.client.force_authenticate(self.auditor)
        response = self.client.get("/api/inspections/9999/")
        self.assertEqual(response.status_code, 404)

    # -- PATCH -----------------------------------------------------------------

    def test_patch_requires_authentication(self):
        """Anonymous PATCH must receive 401."""
        response = self.client.patch(self.url, {}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_patch_forbidden_for_customer(self):
        """Customer PATCH must receive 403."""
        self.client.force_authenticate(self.customer)
        response = self.client.patch(
            self.url, {"responsible": self.auditor.pk}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_patch_updates_responsible(self):
        """
        A valid partial update from an auditor must return 200 and persist
        the change under ``data``.
        """
        auditor2 = _make_account("auditor2", "auditor", "399.650.760-73")
        self.client.force_authenticate(self.auditor)
        response = self.client.patch(
            self.url, {"responsible": auditor2.pk}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.inspection.refresh_from_db()
        self.assertEqual(self.inspection.responsible, auditor2)

    def test_patch_returns_400_when_inspection_is_complete(self):
        """
        Attempting to update an already-complete inspection must return 400
        (the service raises ``ValidationError`` which DRF converts to 400).
        """
        self.inspection.is_complete = True
        self.inspection.save()
        self.client.force_authenticate(self.auditor)
        response = self.client.patch(
            self.url, {"responsible": self.auditor.pk}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_patch_not_found(self):
        """PATCH on an unknown PK must return 404."""
        self.client.force_authenticate(self.auditor)
        response = self.client.patch(
            "/api/inspections/9999/", {"responsible": self.auditor.pk}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    # -- DELETE ----------------------------------------------------------------

    def test_delete_requires_authentication(self):
        """Anonymous DELETE must receive 401."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)

    def test_delete_forbidden_for_customer(self):
        """Customer DELETE must receive 403."""
        self.client.force_authenticate(self.customer)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_delete_allowed_for_auditor(self):
        """
        An auditor deleting an existing inspection must receive 204 and the
        row must no longer exist in the database.
        """
        self.client.force_authenticate(self.auditor)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Inspection.objects.filter(pk=self.inspection.pk).exists())

    def test_delete_not_found(self):
        """DELETE on an unknown PK must return 404."""
        self.client.force_authenticate(self.auditor)
        response = self.client.delete("/api/inspections/9999/")
        self.assertEqual(response.status_code, 404)
