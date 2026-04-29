from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json

from apps.request.models import Request
from apps.request.choices import RequestType
from apps.supply.models import Supply
from apps.supply.choices import SupplyStatus, UnitOfMeasure
from apps.supply_label.models import SupplyLabel

class RequestTestCase(TestCase):


    def setUp(self):
        self.client = Client()

        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )

        # Login user
        self.client.login(username="testuser", password="testpass123")

        # Create Supply dependencies
        self.supply_label = SupplyLabel.objects.create(name="Test Label")

        self.supply = Supply.objects.create(
            supply_label=self.supply_label,
            status=SupplyStatus.AVAILABLE,
            description="Test supply",
            unit_of_measure=UnitOfMeasure.UNIT
        )

        # URLs
        self.list_url = reverse("request:request_list")

    def get_payload(self):
        return {
            "user": self.user.id,
            "request_type": RequestType.ENTRY,
            "supply": self.supply.id,
            "description": "Test request",
            "quantity": 10
        }

    def test_create_request(self):
        response = self.client.post(
            self.list_url,
            data=json.dumps(self.get_payload()),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 201)

        data = json.loads(response.content)
        self.assertIn("data", data)
        self.assertEqual(data["data"]["quantity"], 10)

    def test_list_requests(self):
        Request.objects.create(**self.get_payload())

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn("data", data)
        self.assertEqual(len(data["data"]), 1)

    def test_retrieve_request(self):
        request_obj = Request.objects.create(**self.get_payload())

        url = reverse("request:request_detail", args=[request_obj.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["data"]["id"], request_obj.id)

    def test_update_request(self):
        request_obj = Request.objects.create(**self.get_payload())

        url = reverse("request:request_detail", args=[request_obj.id])

        response = self.client.patch(
            url,
            data=json.dumps({"quantity": 20}),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["data"]["quantity"], 20)

    def test_delete_request(self):
        request_obj = Request.objects.create(**self.get_payload())

        url = reverse("request:request_detail", args=[request_obj.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Request.objects.filter(id=request_obj.id).exists())

    def test_invalid_quantity(self):
        payload = self.get_payload()
        payload["quantity"] = 0

        response = self.client.post(
            self.list_url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_access(self):
        self.client.logout()

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 401)

