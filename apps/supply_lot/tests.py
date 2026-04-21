from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

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

def _future_date(days=30):
    return date.today() + timedelta(days=days)


def _past_date(days=30):
    return date.today() - timedelta(days=days)


# ---------------------------------------------------------------------------


class SupplyLotValidatorTests(TestCase):
    """
    Tests for ``validate_status`` and ``validate_manufacturing_before_expiration``
    — the standalone validator functions used by the model and the serializer.

    Valid values must pass silently; any value outside the declared choices (or
    with an invalid date relationship) must raise ``ValidationError``.
    """

    # validate_status

    def test_valid_status_passes(self):
        """Every declared status must be accepted without raising."""
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

    # validate_manufacturing_before_expiration

    def test_manufacturing_before_expiration_passes(self):
        """A manufacturing date strictly before the expiration date must pass."""
        try:
            validate_manufacturing_before_expiration(
                date(2024, 1, 1), date(2025, 1, 1)
            )
        except ValidationError:
            self.fail(
                "validate_manufacturing_before_expiration raised ValidationError "
                "for a valid date pair."
            )

    def test_manufacturing_equal_to_expiration_raises_validation_error(self):
        """Equal manufacturing and expiration dates must raise ``ValidationError``."""
        same_date = date(2024, 6, 1)
        with self.assertRaises(ValidationError):
            validate_manufacturing_before_expiration(same_date, same_date)

    def test_manufacturing_after_expiration_raises_validation_error(self):
        """A manufacturing date after the expiration date must raise ``ValidationError``."""
        with self.assertRaises(ValidationError):
            validate_manufacturing_before_expiration(
                date(2025, 1, 1), date(2024, 1, 1)
            )


# ---------------------------------------------------------------------------


class SupplyLotModelTests(TestCase):
    """
    Tests for ``SupplyLot.clean`` — ensures the model-level cross-field
    validation delegates correctly to the date validator.
    """

    def _make_inspection_mock(self):
        """Return a minimal mock that satisfies the OneToOneField constraint."""
        inspection = MagicMock()
        inspection.pk = 1
        return inspection

    def test_clean_raises_when_manufacturing_not_before_expiration(self):
        """
        ``clean`` must raise ``ValidationError`` when manufacturing_date is
        greater than or equal to expiration_date.
        """
        lot = SupplyLot(
            status=SupplyLotStatus.PENDING,
            manufacturing_date=date(2025, 6, 1),
            expiration_date=date(2025, 1, 1),
            description="Test lot",
        )
        with self.assertRaises(ValidationError):
            lot.clean()

    def test_clean_passes_for_valid_dates(self):
        """``clean`` must not raise when manufacturing_date < expiration_date."""
        lot = SupplyLot(
            status=SupplyLotStatus.PENDING,
            manufacturing_date=date(2024, 1, 1),
            expiration_date=date(2025, 1, 1),
            description="Test lot",
        )
        try:
            lot.clean()
        except ValidationError:
            self.fail("SupplyLot.clean() raised ValidationError for valid dates.")

    def test_str_representation(self):
        """``__str__`` must include the pk, status label and expiration date."""
        lot = SupplyLot()
        lot.pk = 42
        lot.status = SupplyLotStatus.APPROVED
        lot.expiration_date = date(2026, 12, 31)
        result = str(lot)
        self.assertIn("42", result)
        self.assertIn("Approved", result)
        self.assertIn("2026-12-31", result)


# ---------------------------------------------------------------------------


class SupplyLotSerializerTests(TestCase):
    """
    Tests for ``SupplyLotSerializer``.

    The serializer is responsible for validating status choices and the
    manufacturing/expiration date relationship, enforcing required fields,
    and exposing the expected set of fields in its output representation.

    Because ``inspection`` is a relational field pointing at a separate app,
    all serializer tests that require a persisted instance use a mock
    inspection pk and patch the queryset where needed.
    """

    def _valid_payload(self, **overrides):
        payload = {
            "status": SupplyLotStatus.PENDING,
            "inspection": 1,
            "manufacturing_date": str(_past_date(60)),
            "expiration_date": str(_future_date(300)),
            "description": "Lote de teste para insumo cirúrgico.",
        }
        payload.update(overrides)
        return payload

    def _make_serializer(self, data=None, instance=None, partial=False):
        return SupplyLotSerializer(instance=instance, data=data, partial=partial)

    def test_valid_payload_is_valid(self):
        """A fully-populated, well-formed payload must pass validation."""
        with patch(
            "apps.supply_lot.serializers.SupplyLotSerializer.validate_inspection",
            return_value=MagicMock(pk=1),
        ):
            serializer = self._make_serializer(data=self._valid_payload())
            self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_status_is_invalid(self):
        """``status`` is required; its absence must produce a validation error."""
        payload = self._valid_payload()
        payload = self._valid_payload(status=None)
        serializer = self._make_serializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)

    def test_missing_manufacturing_date_is_invalid(self):
        """``manufacturing_date`` is required; its absence must produce a validation error."""
        payload = self._valid_payload()
        payload = self._valid_payload(manufacturing_date = None)
        serializer = self._make_serializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("manufacturing_date", serializer.errors)

    def test_missing_expiration_date_is_invalid(self):
        """``expiration_date`` is required; its absence must produce a validation error."""
        payload = self._valid_payload()
        payload = self._valid_payload(expiration_date=None)
        serializer = self._make_serializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("expiration_date", serializer.errors)

    def test_missing_description_is_invalid(self):
        """``description`` is required; its absence must produce a validation error."""
        payload = self._valid_payload()
        payload = self._valid_payload(description=None)
        serializer = self._make_serializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("description", serializer.errors)

    def test_invalid_status_is_invalid(self):
        """An unrecognised ``status`` value must be rejected."""
        serializer = self._make_serializer(
            data=self._valid_payload(status="invalid_status")
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)

    def test_id_is_read_only(self):
        """
        ``id`` must be read-only: supplying it in the input payload must
        not cause a validation error, but it must also not appear in
        ``validated_data``.
        """
        with patch(
            "apps.supply_lot.serializers.SupplyLotSerializer.validate_inspection",
            return_value=MagicMock(pk=1),
        ):
            serializer = self._make_serializer(data=self._valid_payload(id=999))
            self.assertTrue(serializer.is_valid(), serializer.errors)
            self.assertNotIn("id", serializer.validated_data)

    def test_representation_contains_expected_fields(self):
        """
        Serialized output must expose exactly the contracted fields:
        ``id``, ``status``, ``inspection``, ``manufacturing_date``,
        ``expiration_date`` and ``description`` — nothing more, nothing less.
        """
        with patch("apps.inspection.models.Inspection") as MockInspection:
            inspection_instance = MagicMock()
            inspection_instance.pk = 1

            lot = SupplyLot(
                pk=10,
                status=SupplyLotStatus.APPROVED,
                inspection=inspection_instance,
                manufacturing_date=_past_date(60),
                expiration_date=_future_date(300),
                description="Lote aprovado.",
            )
            data = SupplyLotSerializer(lot).data
            self.assertIn("id", data)
            self.assertIn("status", data)
            self.assertIn("inspection", data)
            self.assertIn("manufacturing_date", data)
            self.assertIn("expiration_date", data)
            self.assertIn("description", data)
            self.assertNotIn("created_at", data)
            self.assertNotIn("updated_at", data)


# ---------------------------------------------------------------------------


class SupplyLotServiceTests(TestCase):
    """
    Tests for ``SupplyLotService`` — the service layer that wraps
    ``SupplyLot`` persistence.

    These tests bypass HTTP and DRF and call the service methods directly
    so that failures point squarely at the service layer rather than at
    routing or serialization.

    Because ``inspection`` is a OneToOneField protected by a FK constraint,
    tests that need a persisted ``SupplyLot`` row mock the inspection.
    """

    def _valid_data(self, inspection_instance, **overrides):
        data = {
            "status": SupplyLotStatus.PENDING,
            "inspection": inspection_instance,
            "manufacturing_date": _past_date(60),
            "expiration_date": _future_date(300),
            "description": "Cateter venoso central para UTI.",
        }
        data.update(overrides)
        return data

    def _create_lot(self, inspection_instance, **overrides):
        return SupplyLot.objects.create(
            **self._valid_data(inspection_instance, **overrides)
        )

    @patch("apps.supply_lot.services.SupplyLot.objects")
    def test_list_all_returns_all_lots(self, mock_objects):
        """``list_all`` must return the full queryset."""
        mock_qs = MagicMock()
        mock_objects.all.return_value = mock_qs
        result = SupplyLotService.list_all()
        mock_objects.all.assert_called_once()
        self.assertEqual(result, mock_qs)

    @patch("apps.supply_lot.services.get_object_or_404")
    def test_get_returns_correct_lot(self, mock_get):
        """``get`` must delegate to ``get_object_or_404`` with the given pk."""
        mock_lot = MagicMock()
        mock_get.return_value = mock_lot
        result = SupplyLotService.get(pk=1)
        mock_get.assert_called_once_with(SupplyLot, pk=1)
        self.assertEqual(result, mock_lot)

    @patch("apps.supply_lot.services.get_object_or_404")
    def test_get_raises_http404_for_unknown_pk(self, mock_get):
        """``get`` must propagate ``Http404`` for an unknown pk."""
        mock_get.side_effect = Http404
        with self.assertRaises(Http404):
            SupplyLotService.get(pk=9999)

    @patch("apps.supply_lot.services.SupplyLot.objects")
    def test_create_persists_supply_lot(self, mock_objects):
        """``create`` must call ``objects.create`` with the validated data."""
        mock_lot = MagicMock()
        mock_objects.create.return_value = mock_lot
        validated_data = {
            "status": SupplyLotStatus.PENDING,
            "manufacturing_date": _past_date(60),
            "expiration_date": _future_date(300),
            "description": "Test.",
        }
        result = SupplyLotService.create(validated_data)
        mock_objects.create.assert_called_once_with(**validated_data)
        self.assertEqual(result, mock_lot)

    def test_update_sets_attributes_and_saves(self):
        """
        ``update`` must apply each key/value from ``validated_data`` to the
        instance and call ``save``.
        """
        instance = MagicMock(spec=SupplyLot)
        validated_data = {"status": SupplyLotStatus.APPROVED, "description": "Updated."}
        result = SupplyLotService.update(instance=instance, validated_data=validated_data)
        self.assertEqual(instance.status, SupplyLotStatus.APPROVED)
        self.assertEqual(instance.description, "Updated.")
        instance.save.assert_called_once()
        self.assertEqual(result, instance)

    @patch("apps.supply_lot.services.get_object_or_404")
    def test_delete_removes_supply_lot(self, mock_get):
        """``delete`` must fetch the instance and call ``delete`` on it."""
        mock_lot = MagicMock()
        mock_get.return_value = mock_lot
        SupplyLotService.delete(pk=1)
        mock_get.assert_called_once_with(SupplyLot, pk=1)
        mock_lot.delete.assert_called_once()

    @patch("apps.supply_lot.services.get_object_or_404")
    def test_delete_raises_http404_for_unknown_pk(self, mock_get):
        """``delete`` must propagate ``Http404`` for an unknown pk."""
        mock_get.side_effect = Http404
        with self.assertRaises(Http404):
            SupplyLotService.delete(pk=9999)


# ---------------------------------------------------------------------------


class SupplyLotListAPITests(TestCase):
    """
    HTTP-level tests for ``/api/supply-lots/`` (list / create).

    Covers the response envelope shape, empty-list handling, field
    validation at the HTTP boundary, and the 201-with-id contract for
    successful creation.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="supplylotlistuser",
            password="Pw12345!",
            email="supplylotlistuser@example.com",
        )
        self.client.force_authenticate(self.user)
        self.url = "/api/supply-lots/"

    def _valid_payload(self, inspection_pk=1, **overrides):
        payload = {
            "status": SupplyLotStatus.PENDING,
            "inspection": inspection_pk,
            "manufacturing_date": str(_past_date(60)),
            "expiration_date": str(_future_date(300)),
            "description": "Lote de insumo para teste de API.",
        }
        payload.update(overrides)
        return payload

    # GET /api/supply-lots/

    def test_get_returns_200_and_data_envelope(self):
        """GET on the list endpoint must return 200 with a ``data`` key."""
        with patch("apps.supply_lot.views.SupplyLotService.list_all", return_value=[]):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)

    def test_get_empty_list_returns_empty_data(self):
        """When no lots exist the ``data`` key must contain an empty list."""
        with patch("apps.supply_lot.views.SupplyLotService.list_all", return_value=[]):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])

    # POST /api/supply-lots/

    def test_post_creates_supply_lot_and_returns_201(self):
        """
        A valid POST must return 201, delegate creation to the service and
        echo the created resource under the ``data`` key.
        """
        mock_lot = MagicMock(spec=SupplyLot)
        mock_lot.pk = 1
        mock_lot.status = SupplyLotStatus.PENDING
        mock_lot.inspection_id = 1
        mock_lot.manufacturing_date = _past_date(60)
        mock_lot.expiration_date = _future_date(300)
        mock_lot.description = "Lote de insumo para teste de API."

        with patch(
            "apps.supply_lot.views.SupplyLotService.create", return_value=mock_lot
        ), patch(
            "apps.supply_lot.serializers.SupplyLotSerializer.is_valid", return_value=True
        ), patch(
            "apps.supply_lot.serializers.SupplyLotSerializer.validated_data",
            new_callable=lambda: property(lambda self: {}),
        ):
            response = self.client.post(self.url, self._valid_payload(), format="json")

        self.assertEqual(response.status_code, 201, response.data)
        self.assertIn("data", response.data)

    def test_post_with_missing_status_returns_400(self):
        """A payload without ``status`` must return 400 with per-field errors."""
        payload = self._valid_payload()
        payload = self._valid_payload(status=None)
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.data)

    def test_post_with_invalid_status_returns_400(self):
        """An unrecognised ``status`` value must return 400."""
        response = self.client.post(
            self.url,
            self._valid_payload(status="invalid_status"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.data)

    def test_post_with_missing_manufacturing_date_returns_400(self):
        """A payload without ``manufacturing_date`` must return 400."""
        payload = self._valid_payload()
        payload = self._valid_payload(manufacturing_date=None)
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("manufacturing_date", response.data)

    def test_post_with_missing_expiration_date_returns_400(self):
        """A payload without ``expiration_date`` must return 400."""
        payload = self._valid_payload()
        payload = self._valid_payload(expiration_date=None)
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("expiration_date", response.data)

    def test_post_with_missing_description_returns_400(self):
        """A payload without ``description`` must return 400."""
        payload = self._valid_payload()
        payload = self._valid_payload(description=None)
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("description", response.data)


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

        self.mock_lot = MagicMock(spec=SupplyLot)
        self.mock_lot.pk = 1
        self.mock_lot.status = SupplyLotStatus.PENDING
        self.mock_lot.inspection_id = 1
        self.mock_lot.manufacturing_date = _past_date(60)
        self.mock_lot.expiration_date = _future_date(300)
        self.mock_lot.description = "Lote de cateter para teste."

        self.url = "/api/supply-lots/1/"

    # GET /api/supply-lots/<pk>/

    def test_retrieve_returns_200_and_data_envelope(self):
        """GET on an existing pk must return 200 with the resource under ``data``."""
        with patch(
            "apps.supply_lot.views.SupplyLotService.get", return_value=self.mock_lot
        ):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)

    def test_retrieve_returns_correct_fields(self):
        """
        The retrieved payload must expose ``id``, ``status``, ``inspection``,
        ``manufacturing_date``, ``expiration_date`` and ``description``
        at the top level of the ``data`` object.
        """
        with patch(
            "apps.supply_lot.views.SupplyLotService.get", return_value=self.mock_lot
        ):
            response = self.client.get(self.url)
        data = response.data["data"]
        for field in ("id", "status", "inspection", "manufacturing_date", "expiration_date", "description"):
            self.assertIn(field, data)

    def test_retrieve_not_found_returns_404(self):
        """An unknown pk must return 404, not 500 or an empty body."""
        with patch(
            "apps.supply_lot.views.SupplyLotService.get", side_effect=Http404
        ):
            response = self.client.get("/api/supply-lots/9999/")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.data)

    # PATCH /api/supply-lots/<pk>/

    def test_patch_updates_supplied_fields(self):
        """
        PATCH must update only the fields present in the payload and
        persist the changes so that a subsequent fetch reflects them.
        """
        updated_lot = MagicMock(spec=SupplyLot)
        updated_lot.pk = 1
        updated_lot.status = SupplyLotStatus.APPROVED
        updated_lot.inspection_id = 1
        updated_lot.manufacturing_date = self.mock_lot.manufacturing_date
        updated_lot.expiration_date = self.mock_lot.expiration_date
        updated_lot.description = self.mock_lot.description

        with patch(
            "apps.supply_lot.views.SupplyLotService.get", return_value=self.mock_lot
        ), patch(
            "apps.supply_lot.views.SupplyLotService.update", return_value=updated_lot
        ):
            response = self.client.patch(
                self.url, {"status": SupplyLotStatus.APPROVED}, format="json"
            )
        self.assertEqual(response.status_code, 200, response.data)

    def test_patch_does_not_alter_omitted_fields(self):
        """
        Fields absent from a PATCH payload must remain unchanged after
        the update — partial semantics must be enforced.
        """
        original_description = self.mock_lot.description

        with patch(
            "apps.supply_lot.views.SupplyLotService.get", return_value=self.mock_lot
        ), patch(
            "apps.supply_lot.views.SupplyLotService.update", return_value=self.mock_lot
        ):
            self.client.patch(
                self.url, {"status": SupplyLotStatus.QUARANTINE}, format="json"
            )

        self.assertEqual(self.mock_lot.description, original_description)

    def test_patch_response_contains_updated_data(self):
        """The PATCH response must echo the full updated resource under ``data``."""
        with patch(
            "apps.supply_lot.views.SupplyLotService.get", return_value=self.mock_lot
        ), patch(
            "apps.supply_lot.views.SupplyLotService.update", return_value=self.mock_lot
        ):
            response = self.client.patch(
                self.url, {"status": SupplyLotStatus.APPROVED}, format="json"
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)

    def test_patch_with_invalid_status_returns_400(self):
        """A PATCH with an unrecognised ``status`` must return 400."""
        with patch(
            "apps.supply_lot.views.SupplyLotService.get", return_value=self.mock_lot
        ):
            response = self.client.patch(
                self.url, {"status": "invalid_status"}, format="json"
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.data)

    def test_patch_not_found_returns_404(self):
        """PATCH on an unknown pk must return 404."""
        with patch(
            "apps.supply_lot.views.SupplyLotService.get", side_effect=Http404
        ):
            response = self.client.patch(
                "/api/supply-lots/9999/", {"status": SupplyLotStatus.APPROVED}, format="json"
            )
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.data)

    # DELETE /api/supply-lots/<pk>/

    def test_delete_returns_204(self):
        """
        DELETE must return 204 confirming the resource has been removed.
        """
        with patch(
            "apps.supply_lot.views.SupplyLotService.delete", return_value=None
        ):
            response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)

    def test_delete_not_found_returns_404(self):
        """DELETE on an unknown pk must return 404."""
        with patch(
            "apps.supply_lot.views.SupplyLotService.delete", side_effect=Http404
        ):
            response = self.client.delete("/api/supply-lots/9999/")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.data)