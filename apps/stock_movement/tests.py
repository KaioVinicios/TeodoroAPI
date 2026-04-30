from datetime import date, timedelta
import json

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework_simplejwt.tokens import RefreshToken

from apps.inspection.models import Inspection
from apps.request.models import Request
from apps.request.choices import RequestType
from apps.stock_movement.models import StockMovement
from apps.supply.models import Supply
from apps.supply.choices import SupplyStatus, UnitOfMeasure
from apps.supply_label.models import SupplyLabel
from apps.supply_lot.models import SupplyLot
from apps.supply_lot.choices import SupplyLotStatus


class StockMovementTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.defaults["HTTP_AUTHORIZATION"] = (
            f"Bearer {str(refresh.access_token)}"
        )

        self.supply_label = SupplyLabel.objects.create(name="Test Label")
        self.supply = Supply.objects.create(
            supply_label=self.supply_label,
            status=SupplyStatus.AVAILABLE,
            description="Test supply",
            unit_of_measure=UnitOfMeasure.UNIT,
        )

        self.approved_request = Request.objects.create(
            user=self.user,
            request_type=RequestType.ENTRY,
            supply=self.supply,
            description="approved",
            is_approved=True,
            approval_date=date.today(),
            quantity=10,
        )

        self.unapproved_request = Request.objects.create(
            user=self.user,
            request_type=RequestType.ENTRY,
            supply=self.supply,
            description="unapproved",
            is_approved=False,
            quantity=5,
        )

        self.approved_lot = self._make_lot(SupplyLotStatus.APPROVED)

        self.list_url = reverse("stock_movement:stock_movement_list")

    def _make_lot(self, status):
        inspection = Inspection.objects.create(responsible=self.user)
        return SupplyLot.objects.create(
            status=status,
            inspection=inspection,
            manufacturing_date=date.today() - timedelta(days=30),
            expiration_date=date.today() + timedelta(days=365),
            description="lot",
        )

    def _api_payload(self, **overrides):
        payload = {
            "user": self.user.id,
            "supply": self.supply.id,
            "request": self.approved_request.id,
            "supply_lots": [self.approved_lot.id],
            "description": "movement",
        }
        payload.update(overrides)
        return payload

    def _create_movement(self, request=None, lots=None):
        request = request or self.approved_request
        lots = lots or [self.approved_lot]
        movement = StockMovement.objects.create(
            user=self.user,
            supply=self.supply,
            request=request,
            type_of_movement=request.request_type,
            quantity=request.quantity,
            description="seeded",
        )
        movement.supply_lots.set(lots)
        return movement

    def test_create_movement(self):
        response = self.client.post(
            self.list_url,
            data=json.dumps(self._api_payload()),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertIn("data", data)
        self.assertEqual(data["data"]["quantity"], 10)
        self.assertEqual(data["data"]["type_of_movement"], RequestType.ENTRY)
        self.assertEqual(data["data"]["request"], self.approved_request.id)

    def test_create_ignores_client_supplied_quantity_and_type(self):
        payload = self._api_payload()
        payload["quantity"] = 9999
        payload["type_of_movement"] = "EXIT"

        response = self.client.post(
            self.list_url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["data"]["quantity"], 10)
        self.assertEqual(data["data"]["type_of_movement"], RequestType.ENTRY)

    def test_create_rejects_unapproved_request(self):
        response = self.client.post(
            self.list_url,
            data=json.dumps(
                self._api_payload(request=self.unapproved_request.id)
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_create_rejects_non_approved_supply_lots(self):
        pending_lot = self._make_lot(SupplyLotStatus.PENDING)
        response = self.client.post(
            self.list_url,
            data=json.dumps(self._api_payload(supply_lots=[pending_lot.id])),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_create_rejects_empty_supply_lots(self):
        response = self.client.post(
            self.list_url,
            data=json.dumps(self._api_payload(supply_lots=[])),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_rejects_already_consumed_request(self):
        self._create_movement()
        response = self.client.post(
            self.list_url,
            data=json.dumps(self._api_payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(StockMovement.objects.count(), 1)

    def test_list_movements(self):
        self._create_movement()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["data"]), 1)

    def test_retrieve_movement(self):
        movement = self._create_movement()
        url = reverse("stock_movement:stock_movement_detail", args=[movement.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["data"]["id"], movement.id)

    def test_retrieve_unknown_returns_404(self):
        url = reverse("stock_movement:stock_movement_detail", args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content), {"error": "Stock movement not found"}
        )

    def test_patch_updates_only_description(self):
        movement = self._create_movement()
        url = reverse("stock_movement:stock_movement_detail", args=[movement.id])

        response = self.client.patch(
            url,
            data=json.dumps({"description": "updated text", "quantity": 9999}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["data"]["description"], "updated text")
        self.assertEqual(data["data"]["quantity"], movement.quantity)

        movement.refresh_from_db()
        self.assertEqual(movement.description, "updated text")
        self.assertEqual(movement.quantity, 10)

    def test_patch_does_not_change_supply(self):
        movement = self._create_movement()
        other_supply = Supply.objects.create(
            supply_label=self.supply_label,
            status=SupplyStatus.AVAILABLE,
            description="other",
            unit_of_measure=UnitOfMeasure.UNIT,
        )
        url = reverse("stock_movement:stock_movement_detail", args=[movement.id])

        response = self.client.patch(
            url,
            data=json.dumps({"supply": other_supply.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        movement.refresh_from_db()
        self.assertEqual(movement.supply_id, self.supply.id)

    def test_unauthenticated_access(self):
        self.client.defaults.pop("HTTP_AUTHORIZATION", None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 401)
