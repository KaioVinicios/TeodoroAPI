from django.http import Http404
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
    OpenApiResponse,
)

from apps.supply.services import SupplyLabelServices, SupplyServices
from apps.supply.serializers import SupplyLabelSerializer, SupplySerializer
from apps.account.permissions import IsNotCustomer


# ── Envelope helpers ──────────────────────────────────────────────────────────

SupplyLabelEnvelopeSerializer = inline_serializer(
    name="SupplyLabelEnvelope",
    fields={"data": SupplyLabelSerializer()},
)
SupplyLabelListEnvelopeSerializer = inline_serializer(
    name="SupplyLabelListEnvelope",
    fields={"data": SupplyLabelSerializer(many=True)},
)

SupplyEnvelopeSerializer = inline_serializer(
    name="SupplyEnvelope",
    fields={"data": SupplySerializer()},
)
SupplyListEnvelopeSerializer = inline_serializer(
    name="SupplyListEnvelope",
    fields={"data": SupplySerializer(many=True)},
)

ErrorResponseSerializer = inline_serializer(
    name="SupplyErrorResponse",
    fields={"error": serializers.CharField()},
)


# ── Supply Label views ────────────────────────────────────────────────────────

@extend_schema(tags=["supply-labels"])
@extend_schema_view(
    get=extend_schema(
        operation_id="supply_labels_list",
        summary="List supply labels",
        description="Returns all supply labels registered in the system.",
        responses={
            200: SupplyLabelListEnvelopeSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
    ),
    post=extend_schema(
        operation_id="supply_labels_create",
        summary="Create supply label",
        description="Creates a new supply label. Restricted to non-customer users.",
        request=SupplyLabelSerializer,
        responses={
            201: SupplyLabelEnvelopeSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="Customers cannot access this resource."),
        },
    ),
)
class SupplyLabelListAPIView(APIView):
    serializer_class = SupplyLabelSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsNotCustomer()]
        return [IsAuthenticated()]

    def get(self, request):
        labels = SupplyLabelServices.list_all()
        serializer = SupplyLabelSerializer(labels, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SupplyLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        label = SupplyLabelServices.create(serializer.validated_data)
        response = SupplyLabelSerializer(label)
        return Response({"data": response.data}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["supply-labels"])
@extend_schema_view(
    get=extend_schema(
        operation_id="supply_labels_retrieve",
        summary="Retrieve supply label",
        responses={
            200: SupplyLabelEnvelopeSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Supply label not found."),
        },
    ),
    patch=extend_schema(
        operation_id="supply_labels_partial_update",
        summary="Partially update supply label",
        request=SupplyLabelSerializer,
        responses={
            200: SupplyLabelEnvelopeSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="Customers cannot access this resource."),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Supply label not found."),
        },
    ),
    delete=extend_schema(
        operation_id="supply_labels_destroy",
        summary="Delete supply label",
        responses={
            204: OpenApiResponse(description="Supply label deleted."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="Customers cannot access this resource."),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Supply label not found."),
        },
    ),
)
class SupplyLabelDetailAPIView(APIView):
    serializer_class = SupplyLabelSerializer

    def get_permissions(self):
        if self.request.method in ("PATCH", "DELETE"):
            return [IsAuthenticated(), IsNotCustomer()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        try:
            label = SupplyLabelServices.get(pk)
        except Http404:
            return Response({"error": "Supply label not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = SupplyLabelSerializer(label)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        try:
            label = SupplyLabelServices.get(pk)
        except Http404:
            return Response({"error": "Supply label not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = SupplyLabelSerializer(label, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = SupplyLabelServices.update(label, serializer.validated_data)
        response = SupplyLabelSerializer(updated)
        return Response({"data": response.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            SupplyLabelServices.delete(pk)
        except Http404:
            return Response({"error": "Supply label not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Supply views ──────────────────────────────────────────────────────────────

@extend_schema(tags=["supplies"])
@extend_schema_view(
    get=extend_schema(
        operation_id="supplies_list",
        summary="List supplies",
        description="Returns all supplies registered in the system.",
        responses={
            200: SupplyListEnvelopeSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
    ),
    post=extend_schema(
        operation_id="supplies_create",
        summary="Create supply",
        description="Creates a new supply entry. Restricted to non-customer users.",
        request=SupplySerializer,
        responses={
            201: SupplyEnvelopeSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="Customers cannot access this resource."),
        },
    ),
)
class SupplyListAPIView(APIView):
    serializer_class = SupplySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsNotCustomer()]
        return [IsAuthenticated()]

    def get(self, request):
        supplies = SupplyServices.list_all()
        serializer = SupplySerializer(supplies, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SupplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supply = SupplyServices.create(serializer.validated_data)
        response = SupplySerializer(supply)
        return Response({"data": response.data}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["supplies"])
@extend_schema_view(
    get=extend_schema(
        operation_id="supplies_retrieve",
        summary="Retrieve supply",
        responses={
            200: SupplyEnvelopeSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Supply not found."),
        },
    ),
    patch=extend_schema(
        operation_id="supplies_partial_update",
        summary="Partially update supply",
        request=SupplySerializer,
        responses={
            200: SupplyEnvelopeSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="Customers cannot access this resource."),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Supply not found."),
        },
    ),
    delete=extend_schema(
        operation_id="supplies_destroy",
        summary="Delete supply",
        responses={
            204: OpenApiResponse(description="Supply deleted."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="Customers cannot access this resource."),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Supply not found."),
        },
    ),
)
class SupplyDetailAPIView(APIView):
    serializer_class = SupplySerializer

    def get_permissions(self):
        if self.request.method in ("PATCH", "DELETE"):
            return [IsAuthenticated(), IsNotCustomer()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        try:
            supply = SupplyServices.get(pk)
        except Http404:
            return Response({"error": "Supply not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = SupplySerializer(supply)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        try:
            supply = SupplyServices.get(pk)
        except Http404:
            return Response({"error": "Supply not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = SupplySerializer(supply, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = SupplyServices.update(supply, serializer.validated_data)
        response = SupplySerializer(updated)
        return Response({"data": response.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            SupplyServices.delete(pk)
        except Http404:
            return Response({"error": "Supply not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)