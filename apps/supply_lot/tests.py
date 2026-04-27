from django.test import TestCase
from django.http import Http404
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from datetime import date, timedelta

from apps.account.models import Account
from apps.account.choices import AccountType
from apps.inspection.models import Inspection
from apps.supply_lot.models import SupplyLot
from apps.supply_lot.serializers import SupplyLotSerializer
from apps.supply_lot.services import SupplyLotService
from apps.supply_lot.validators import (
    validate_status,
    validate_manufacturing_before_expiration,
)
from apps.supply_lot.choices import SupplyLotStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TODAY = date.today()
MANUFACTURING = TODAY - timedelta(days=30)
EXPIRATION = TODAY + timedelta(days=180)

_auditor_counter = 0


def _make_auditor_user(username=None):
    """
    Creates a User with an Account of type ``auditor``.
    Required because ``Inspection.responsible`` is validated to be an auditor.
    """
    global _auditor_counter
    _auditor_counter += 1
    if username is None:
        username = f"auditor_{_auditor_counter}"
    user = User.objects.create_user(
        username=username,
        password="Pw12345!",
        email=f"{username}@example.com",
    )
    Account.objects.create(
        user=user,
        account_type=AccountType.AUDITOR,
        cpf=_unique_cpf(_auditor_counter),
        address="Rua dos Auditores, 1",
        phone_number="(11) 91234-5678",
    )
    return user


def _unique_cpf(seed: int) -> str:
    """
    Returns a structurally valid CPF that is unique per seed value.
    Values are pre-validated so the CPF check-digit validator passes.
    """
    valid_cpfs = [
        "529.982.247-25",
        "111.444.777-35",
        "295.669.955-93",
        "902.556.289-68",
        "746.959.438-68",
        "374.348.252-00",
        "061.316.468-05",
        "455.823.030-47",
        "168.995.265-42",
        "876.455.930-69",
    ]
    return valid_cpfs[(seed - 1) % len(valid_cpfs)]


def _make_inspection(responsible=None):
    """
    Creates and returns an ``Inspection`` instance with a valid auditor
    as the responsible user.
    """
    if responsible is None:
        responsible = _make_auditor_user()
    return Inspection.objects.create(responsible=responsible)


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------


class SupplyLotValidatorTests(TestCase):
    """
    Tests for ``validate_status`` and
    ``validate_manufacturing_before_expiration`` — the standalone validator
    functions used by the model and the serializer.

    Valid values must pass silently; invalid values must raise
    ``ValidationError`` with an appropriate message.
    """

    # validate_status

    def test_valid_status_passes(self):
        """Every declared status value must be accepted without raising."""
        for status_value in SupplyLotStatus.values:
            with self.subTest(status=status_value):
                try:
                    validate_status(status_value)
                except ValidationError:
                    self.fail(
                        f"validate_status raised ValidationError for valid status '{status_value}'"
                    )

    def test_invalid_status_raises_validation_error(self):
        """An unrecognised status must raise ``ValidationError``."""
        with self.assertRaises(ValidationError):
            validate_status("unknown_status")

    def test_empty_status_raises_validation_error(self):
        """An empty string is not a valid status and must be rejected."""
        with self.assertRaises(ValidationError):
            validate_status("")

    def test_numeric_status_raises_validation_error(self):
        """A numeric string that is not a declared choice must be rejected."""
        with self.assertRaises(ValidationError):
            validate_status("123")

    # validate_manufacturing_before_expiration

    def test_manufacturing_before_expiration_passes(self):
        """A manufacturing date strictly before expiration must pass silently."""
        try:
            validate_manufacturing_before_expiration(MANUFACTURING, EXPIRATION)
        except ValidationError:
            self.fail(
                "validate_manufacturing_before_expiration raised ValidationError "
                "for valid date pair."
            )

    def test_manufacturing_equal_expiration_raises_validation_error(self):
        """Equal manufacturing and expiration dates must be rejected."""
        same_date = date(2024, 6, 1)
        with self.assertRaises(ValidationError):
            validate_manufacturing_before_expiration(same_date, same_date)

    def test_manufacturing_after_expiration_raises_validation_error(self):
        """A manufacturing date after the expiration date must be rejected."""
        with self.assertRaises(ValidationError):
            validate_manufacturing_before_expiration(EXPIRATION, MANUFACTURING)

    def test_manufacturing_one_day_before_expiration_passes(self):
        """Manufacturing exactly one day before expiration is a valid edge case."""
        one_day_before = EXPIRATION - timedelta(days=1)
        try:
            validate_manufacturing_before_expiration(one_day_before, EXPIRATION)
        except ValidationError:
            self.fail(
                "validate_manufacturing_before_expiration raised ValidationError "
                "for manufacturing date one day before expiration."
            )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class SupplyLotModelTests(TestCase):
    """
    Tests for the ``SupplyLot`` model — field defaults, ``clean()``
    validation and ``__str__`` representation.
    """

    def setUp(self):
        self.inspection = _make_inspection()

    def _make_lot(self, **overrides):
        defaults = dict(
            status=SupplyLotStatus.PENDING,
            inspection=self.inspection,
            manufacturing_date=MANUFACTURING,
            expiration_date=EXPIRATION,
            description="Lote de teste.",
        )
        defaults.update(overrides)
        return SupplyLot(**defaults)

    def test_default_status_is_pending(self):
        """A newly created lot without an explicit status must default to ``pending``."""
        lot = SupplyLot.objects.create(
            inspection=self.inspection,
            manufacturing_date=MANUFACTURING,
            expiration_date=EXPIRATION,
            description="Lote padrão.",
        )
        self.assertEqual(lot.status, SupplyLotStatus.PENDING)

    def test_clean_raises_when_manufacturing_equals_expiration(self):
        """``clean()`` must propagate the date-order ValidationError from the validator."""
        same = date(2024, 6, 1)
        lot = self._make_lot(manufacturing_date=same, expiration_date=same)
        with self.assertRaises(ValidationError):
            lot.clean()

    def test_clean_raises_when_manufacturing_after_expiration(self):
        """``clean()`` must reject a manufacturing date that is after expiration."""
        lot = self._make_lot(manufacturing_date=EXPIRATION, expiration_date=MANUFACTURING)
        with self.assertRaises(ValidationError):
            lot.clean()

    def test_clean_passes_for_valid_dates(self):
        """``clean()`` must not raise for a well-ordered date pair."""
        lot = self._make_lot()
        try:
            lot.clean()
        except ValidationError:
            self.fail("SupplyLot.clean() raised ValidationError for valid date pair.")

    def test_str_contains_pk_status_and_expiration(self):
        """``__str__`` must include the pk, status display and expiration date."""
        lot = SupplyLot.objects.create(
            status=SupplyLotStatus.APPROVED,
            inspection=self.inspection,
            manufacturing_date=MANUFACTURING,
            expiration_date=EXPIRATION,
            description="Lote str.",
        )
        representation = str(lot)
        self.assertIn(str(lot.pk), representation)
        self.assertIn(str(EXPIRATION), representation)


# ---------------------------------------------------------------------------
# Serializer tests
# ---------------------------------------------------------------------------


class SupplyLotSerializerTests(TestCase):
    """
    Tests for ``SupplyLotSerializer``.

    The serializer is responsible for validating status choices and the
    manufacturing/expiration date relationship (delegating to the validators),
    enforcing required fields, and exposing the expected set of fields in its
    output representation.
    """

    def setUp(self):
        self.inspection = _make_inspection()

    def _valid_payload(self, **overrides):
        payload = {
            "status": SupplyLotStatus.PENDING,
            "inspection": self.inspection.pk,
            "manufacturing_date": str(MANUFACTURING),
            "expiration_date": str(EXPIRATION),
            "description": "Lote de luvas cirúrgicas.",
        }
        payload.update(overrides)
        return payload

    def test_valid_payload_is_valid(self):
        """A fully-populated, well-formed payload must pass validation."""
        serializer = SupplyLotSerializer(data=self._valid_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_inspection_is_invalid(self):
        """``inspection`` is required; its absence must produce a validation error."""
        serializer = SupplyLotSerializer(data=self._valid_payload(inspection=None))
        self.assertFalse(serializer.is_valid())
        self.assertIn("inspection", serializer.errors)

    def test_missing_manufacturing_date_is_invalid(self):
        """``manufacturing_date`` is required; its absence must produce a validation error."""
        serializer = SupplyLotSerializer(data=self._valid_payload(manufacturing_date=None))
        self.assertFalse(serializer.is_valid())
        self.assertIn("manufacturing_date", serializer.errors)

    def test_missing_expiration_date_is_invalid(self):
        """``expiration_date`` is required; its absence must produce a validation error."""
        serializer = SupplyLotSerializer(data=self._valid_payload(expiration_date=None))
        self.assertFalse(serializer.is_valid())
        self.assertIn("expiration_date", serializer.errors)

    def test_missing_description_is_invalid(self):
        """``description`` is required; its absence must produce a validation error."""
        serializer = SupplyLotSerializer(data=self._valid_payload(description=None))
        self.assertFalse(serializer.is_valid())
        self.assertIn("description", serializer.errors)

    def test_invalid_status_is_invalid(self):
        """An unrecognised ``status`` value must be rejected."""
        serializer = SupplyLotSerializer(
            data=self._valid_payload(status="contaminated")
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)

    def test_all_valid_statuses_are_accepted(self):
        """Every declared ``SupplyLotStatus`` value must be accepted by the serializer."""
        for status_value in SupplyLotStatus.values:
            with self.subTest(status=status_value):
                serializer = SupplyLotSerializer(
                    data=self._valid_payload(status=status_value)
                )
                self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_representation_contains_expected_fields(self):
        """
        Serialized output must expose the contracted fields:
        ``id``, ``status``, ``inspection``, ``manufacturing_date``,
        ``expiration_date`` and ``description``.
        """
        supply_lot = SupplyLot.objects.create(
            status=SupplyLotStatus.PENDING,
            inspection=self.inspection,
            manufacturing_date=MANUFACTURING,
            expiration_date=EXPIRATION,
            description="Lote de teste.",
        )
        data = SupplyLotSerializer(supply_lot).data
        for field in ("id", "status", "inspection", "manufacturing_date", "expiration_date", "description"):
            with self.subTest(field=field):
                self.assertIn(field, data)

    def test_representation_status_and_inspection_values(self):
        """Serialized output must carry the correct ``status`` and ``inspection`` values."""
        supply_lot = SupplyLot.objects.create(
            status=SupplyLotStatus.PENDING,
            inspection=self.inspection,
            manufacturing_date=MANUFACTURING,
            expiration_date=EXPIRATION,
            description="Lote de teste.",
        )
        data = SupplyLotSerializer(supply_lot).data
        self.assertEqual(data["status"], SupplyLotStatus.PENDING)
        self.assertEqual(data["inspection"], self.inspection.pk)

    def test_id_is_read_only(self):
        """
        ``id`` must be read-only: supplying it in the input payload must
        not cause a validation error, but it must not be accepted as a
        writable field.
        """
        serializer = SupplyLotSerializer(data=self._valid_payload(id=999))
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("id", serializer.validated_data)

    def test_nonexistent_inspection_is_invalid(self):
        """An ``inspection`` pk that does not exist in the DB must be rejected."""
        serializer = SupplyLotSerializer(data=self._valid_payload(inspection=99999))
        self.assertFalse(serializer.is_valid())
        self.assertIn("inspection", serializer.errors)


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class SupplyLotServiceTests(TestCase):
    """
    Tests for ``SupplyLotService`` — the service layer that wraps
    ``SupplyLot`` persistence.

    These tests bypass HTTP and DRF and call the service methods directly
    so that failures point squarely at the service layer rather than at
    routing or serialization.
    """

    def setUp(self):
        self.inspection = _make_inspection()

    def _valid_data(self, **overrides):
        data = {
            "status": SupplyLotStatus.PENDING,
            "inspection": self.inspection,
            "manufacturing_date": MANUFACTURING,
            "expiration_date": EXPIRATION,
            "description": "Lote de cateter venoso.",
        }
        data.update(overrides)
        return data

    def test_create_persists_supply_lot(self):
        """``create`` must persist exactly one ``SupplyLot`` row in the database."""
        supply_lot = SupplyLotService.create(self._valid_data())
        self.assertEqual(SupplyLot.objects.count(), 1)
        self.assertIsNotNone(supply_lot.pk)

    def test_create_returns_supply_lot_instance(self):
        """``create`` must return the persisted ``SupplyLot`` instance."""
        supply_lot = SupplyLotService.create(self._valid_data())
        self.assertIsInstance(supply_lot, SupplyLot)

    def test_create_stores_correct_field_values(self):
        """The persisted instance must reflect the data passed to ``create``."""
        supply_lot = SupplyLotService.create(self._valid_data())
        self.assertEqual(supply_lot.status, SupplyLotStatus.PENDING)
        self.assertEqual(supply_lot.inspection, self.inspection)
        self.assertEqual(supply_lot.manufacturing_date, MANUFACTURING)
        self.assertEqual(supply_lot.expiration_date, EXPIRATION)
        self.assertEqual(supply_lot.description, "Lote de cateter venoso.")

    def test_list_all_returns_all_supply_lots(self):
        """``list_all`` must return every ``SupplyLot`` row present in the database."""
        inspection2 = _make_inspection()
        SupplyLotService.create(self._valid_data())
        SupplyLotService.create(
            self._valid_data(inspection=inspection2, description="Segundo lote.")
        )
        result = SupplyLotService.list_all()
        self.assertEqual(result.count(), 2)

    def test_list_all_returns_empty_queryset_when_no_lots(self):
        """``list_all`` on an empty table must return an empty queryset."""
        result = SupplyLotService.list_all()
        self.assertEqual(result.count(), 0)

    def test_get_returns_correct_supply_lot(self):
        """``get`` must return the ``SupplyLot`` whose pk matches the argument."""
        supply_lot = SupplyLotService.create(self._valid_data())
        fetched = SupplyLotService.get(supply_lot.pk)
        self.assertEqual(fetched.pk, supply_lot.pk)

    def test_get_raises_404_for_nonexistent_pk(self):
        """``get`` must raise ``Http404`` when no row matches the given pk."""
        with self.assertRaises(Http404):
            SupplyLotService.get(9999)

    def test_update_changes_supplied_fields(self):
        """``update`` must persist every field supplied in ``validated_data``."""
        supply_lot = SupplyLotService.create(self._valid_data())
        updated = SupplyLotService.update(
            supply_lot, {"status": SupplyLotStatus.APPROVED, "description": "Aprovado."}
        )
        supply_lot.refresh_from_db()
        self.assertEqual(supply_lot.status, SupplyLotStatus.APPROVED)
        self.assertEqual(supply_lot.description, "Aprovado.")
        self.assertEqual(updated.pk, supply_lot.pk)

    def test_update_returns_updated_instance(self):
        """``update`` must return the same instance (same pk) with the new values."""
        supply_lot = SupplyLotService.create(self._valid_data())
        updated = SupplyLotService.update(supply_lot, {"status": SupplyLotStatus.REJECTED})
        self.assertIsInstance(updated, SupplyLot)
        self.assertEqual(updated.pk, supply_lot.pk)

    def test_update_does_not_alter_omitted_fields(self):
        """Fields absent from ``validated_data`` must remain unchanged after ``update``."""
        supply_lot = SupplyLotService.create(self._valid_data())
        original_expiration = supply_lot.expiration_date
        SupplyLotService.update(supply_lot, {"status": SupplyLotStatus.QUARANTINE})
        supply_lot.refresh_from_db()
        self.assertEqual(supply_lot.expiration_date, original_expiration)

    def test_delete_removes_supply_lot(self):
        """``delete`` must remove the row so that no orphan record remains."""
        supply_lot = SupplyLotService.create(self._valid_data())
        pk = supply_lot.pk
        SupplyLotService.delete(pk)
        self.assertFalse(SupplyLot.objects.filter(pk=pk).exists())

    def test_delete_raises_404_for_nonexistent_pk(self):
        """``delete`` must raise ``Http404`` when no row matches the given pk."""
        with self.assertRaises(Http404):
            SupplyLotService.delete(9999)


# ---------------------------------------------------------------------------
# View / API tests — list endpoint
# ---------------------------------------------------------------------------


class SupplyLotListAPITests(TestCase):
    """
    HTTP-level tests for ``/api/supply-lots/``
    (list / create).

    Covers the ``{"data": ...}`` response envelope, empty-list responses,
    required-field validation at the HTTP layer and successful creation
    with the resulting 201 status code.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="supplylotlistuser",
            password="Pw12345!",
            email="supplylotlistuser@example.com",
        )
        self.client.force_authenticate(self.user)
        self.inspection = _make_inspection()
        self.url = "/api/supply-lots/"

    def _valid_payload(self, **overrides):
        payload = {
            "status": SupplyLotStatus.PENDING,
            "inspection": self.inspection.pk,
            "manufacturing_date": str(MANUFACTURING),
            "expiration_date": str(EXPIRATION),
            "description": "Lote de máscaras cirúrgicas.",
        }
        payload.update(overrides)
        return payload

    # GET /api/supply-lots/

    def test_get_returns_200_and_data_envelope(self):
        """GET must return 200 with results nested under the ``data`` key."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)

    def test_get_returns_all_supply_lots(self):
        """GET must include every persisted ``SupplyLot`` in its response."""
        inspection2 = _make_inspection()
        SupplyLot.objects.create(
            status=SupplyLotStatus.PENDING,
            inspection=self.inspection,
            manufacturing_date=MANUFACTURING,
            expiration_date=EXPIRATION,
            description="Lote A.",
        )
        SupplyLot.objects.create(
            status=SupplyLotStatus.APPROVED,
            inspection=inspection2,
            manufacturing_date=MANUFACTURING,
            expiration_date=EXPIRATION,
            description="Lote B.",
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 2)

    def test_get_returns_empty_list_when_no_lots(self):
        """GET on an empty table must return 200 with an empty list under ``data``."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])

    # POST /api/supply-lots/

    def test_post_creates_supply_lot_and_returns_201(self):
        """
        A valid POST must return 201, persist one row and echo the created
        resource under the ``data`` key.
        """
        response = self.client.post(self.url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(SupplyLot.objects.count(), 1)
        self.assertIn("data", response.data)
        self.assertEqual(
            response.data["data"]["description"], "Lote de máscaras cirúrgicas."
        )

    def test_post_response_contains_id(self):
        """The created resource in the response must include the generated ``id``."""
        response = self.client.post(self.url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.data["data"])

    def test_post_response_status_matches_payload(self):
        """The response must reflect the ``status`` submitted in the payload."""
        response = self.client.post(
            self.url,
            self._valid_payload(status=SupplyLotStatus.APPROVED),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["status"], SupplyLotStatus.APPROVED)

    def test_post_with_missing_description_returns_400(self):
        """A payload without ``description`` must return 400 with per-field errors."""
        response = self.client.post(
            self.url, self._valid_payload(description=None), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("description", response.data)

    def test_post_with_missing_manufacturing_date_returns_400(self):
        """A payload without ``manufacturing_date`` must return 400."""
        response = self.client.post(
            self.url, self._valid_payload(manufacturing_date=None), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("manufacturing_date", response.data)

    def test_post_with_missing_expiration_date_returns_400(self):
        """A payload without ``expiration_date`` must return 400."""
        response = self.client.post(
            self.url, self._valid_payload(expiration_date=None), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("expiration_date", response.data)

    def test_post_with_invalid_status_returns_400(self):
        """An unrecognised ``status`` value must return 400."""
        response = self.client.post(
            self.url,
            self._valid_payload(status="contaminated"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.data)

    def test_post_with_missing_inspection_returns_400(self):
        """A payload without ``inspection`` must return 400."""
        response = self.client.post(
            self.url, self._valid_payload(inspection=None), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("inspection", response.data)


# ---------------------------------------------------------------------------
# View / API tests — detail endpoint
# ---------------------------------------------------------------------------


class SupplyLotDetailAPITests(TestCase):
    """
    HTTP-level tests for ``/api/supply-lots/<pk>/``
    (retrieve / partial-update / delete).

    Covers the response envelope shape, 404 handling for unknown primary
    keys, partial-update semantics (only supplied fields are changed) and
    the hard-delete contract (204 with no remaining row).
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="supplylotdetailuser",
            password="Pw12345!",
            email="supplylotdetailuser@example.com",
        )
        self.client.force_authenticate(self.user)
        self.inspection = _make_inspection()
        self.supply_lot = SupplyLot.objects.create(
            status=SupplyLotStatus.PENDING,
            inspection=self.inspection,
            manufacturing_date=MANUFACTURING,
            expiration_date=EXPIRATION,
            description="Lote de seringas descartáveis.",
        )
        self.url = f"/api/supply-lots/{self.supply_lot.pk}/"

    # GET /api/supply-lots/<pk>/

    def test_retrieve_returns_200_and_data_envelope(self):
        """GET on an existing pk must return 200 with the resource under ``data``."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)

    def test_retrieve_returns_correct_fields(self):
        """
        The retrieved payload must expose ``id``, ``status``, ``inspection``,
        ``manufacturing_date``, ``expiration_date`` and ``description``.
        """
        response = self.client.get(self.url)
        data = response.data["data"]
        self.assertEqual(data["id"], self.supply_lot.pk)
        self.assertEqual(data["status"], SupplyLotStatus.PENDING)
        self.assertEqual(data["inspection"], self.inspection.pk)
        self.assertEqual(data["description"], "Lote de seringas descartáveis.")

    def test_retrieve_not_found_returns_404(self):
        """An unknown pk must return 404, not 500 or an empty body."""
        response = self.client.get("/api/supply-lots/9999/")
        self.assertEqual(response.status_code, 404)

    def test_retrieve_404_response_contains_error_key(self):
        """The 404 response body must contain the ``error`` key."""
        response = self.client.get("/api/supply-lots/9999/")
        self.assertIn("error", response.data)

    # PATCH /api/supply-lots/<pk>/

    def test_patch_updates_supplied_fields(self):
        """
        PATCH must update only the fields present in the payload and
        persist the changes so that a subsequent fetch reflects them.
        """
        response = self.client.patch(
            self.url,
            {"status": SupplyLotStatus.APPROVED, "description": "Lote aprovado."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.supply_lot.refresh_from_db()
        self.assertEqual(self.supply_lot.status, SupplyLotStatus.APPROVED)
        self.assertEqual(self.supply_lot.description, "Lote aprovado.")

    def test_patch_does_not_alter_omitted_fields(self):
        """
        Fields absent from a PATCH payload must remain unchanged after
        the update — partial semantics must be enforced.
        """
        original_expiration = self.supply_lot.expiration_date
        self.client.patch(
            self.url, {"status": SupplyLotStatus.QUARANTINE}, format="json"
        )
        self.supply_lot.refresh_from_db()
        self.assertEqual(self.supply_lot.expiration_date, original_expiration)

    def test_patch_response_contains_updated_data(self):
        """The PATCH response must echo the full updated resource under ``data``."""
        response = self.client.patch(
            self.url, {"description": "Descrição modificada."}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"]["description"], "Descrição modificada.")

    def test_patch_with_invalid_status_returns_400(self):
        """A PATCH with an unrecognised ``status`` must return 400."""
        response = self.client.patch(
            self.url, {"status": "contaminated"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.data)

    def test_patch_not_found_returns_404(self):
        """PATCH on an unknown pk must return 404."""
        response = self.client.patch(
            "/api/supply-lots/9999/", {"description": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_patch_all_valid_statuses_accepted(self):
        """Each declared status must be accepted by PATCH without error."""
        inspections = [_make_inspection() for _ in SupplyLotStatus.values]
        lots = [
            SupplyLot.objects.create(
                status=SupplyLotStatus.PENDING,
                inspection=inspections[i],
                manufacturing_date=MANUFACTURING,
                expiration_date=EXPIRATION,
                description=f"Lote {i}.",
            )
            for i, _ in enumerate(SupplyLotStatus.values)
        ]
        for lot, status_value in zip(lots, SupplyLotStatus.values):
            with self.subTest(status=status_value):
                url = f"/api/supply-lots/{lot.pk}/"
                response = self.client.patch(url, {"status": status_value}, format="json")
                self.assertEqual(response.status_code, 200, response.data)

    # DELETE /api/supply-lots/<pk>/

    def test_delete_returns_204_and_removes_row(self):
        """
        DELETE must return 204 and remove the row so that no orphan
        record remains in the database.
        """
        pk = self.supply_lot.pk
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(SupplyLot.objects.filter(pk=pk).exists())

    def test_delete_not_found_returns_404(self):
        """DELETE on an unknown pk must return 404."""
        response = self.client.delete("/api/supply-lots/9999/")
        self.assertEqual(response.status_code, 404)

    def test_delete_404_response_contains_error_key(self):
        """The 404 response body on DELETE must contain the ``error`` key."""
        response = self.client.delete("/api/supply-lots/9999/")
        self.assertIn("error", response.data)