from django.core.exceptions import ValidationError as DjangoValidationError
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
from apps.stock_movement.serializers import StockMovementSerializer
from apps.stock_movement.services import StockMovementServices


StockMovementEnvelopeSerializer = inline_serializer(
    name="StockMovementEnvelope",
    fields={"data": StockMovementSerializer()},
)

StockMovementListEnvelopeSerializer = inline_serializer(
    name="StockMovementListEnvelope",
    fields={"data": StockMovementSerializer(many=True)},
)

ErrorResponseSerializer = inline_serializer(
    name="StockMovementErrorResponse",
    fields={"error": serializers.CharField()},
)


@extend_schema(tags=["stock-movements"])
@extend_schema_view(
    get=extend_schema(
        operation_id="stock_movements_list",
        summary="List stock movements",
        description="Returns all stock movements. Requires authentication.",
        responses={
            200: StockMovementListEnvelopeSerializer,
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
    ),
    post=extend_schema(
        operation_id="stock_movements_create",
        summary="Create stock movement",
        description=(
            "Creates a stock movement from an approved request. "
            "Both `type_of_movement` and `quantity` are derived from the request "
            "and cannot be supplied by the client."
        ),
        request=StockMovementSerializer,
        responses={
            201: StockMovementEnvelopeSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
    ),
)
class StockMovementListAPIView(APIView):
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        movements = StockMovementServices.list_all()
        serializer = StockMovementSerializer(movements, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = StockMovementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            movement = StockMovementServices.create(serializer.validated_data)
        except DjangoValidationError as exc:
            return Response(
                {"error": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response = StockMovementSerializer(movement)
        return Response({"data": response.data}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["stock-movements"])
@extend_schema_view(
    get=extend_schema(
        operation_id="stock_movements_retrieve",
        summary="Retrieve stock movement",
        description="Returns a single stock movement by ID.",
        responses={
            200: StockMovementEnvelopeSerializer,
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Stock movement not found.",
            ),
        },
    ),
    patch=extend_schema(
        operation_id="stock_movements_partial_update",
        summary="Partially update stock movement",
        description=(
            "Updates a stock movement. Only `description` may be modified after "
            "creation; all other fields are immutable."
        ),
        request=StockMovementSerializer,
        responses={
            200: StockMovementEnvelopeSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Stock movement not found.",
            ),
        },
    ),
)
class StockMovementDetailAPIView(APIView):
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            movement = StockMovementServices.get(pk)
        except Http404:
            return Response(
                {"error": "Stock movement not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = StockMovementSerializer(movement)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        try:
            movement = StockMovementServices.get(pk)
        except Http404:
            return Response(
                {"error": "Stock movement not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = StockMovementSerializer(
            movement, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        try:
            updated = StockMovementServices.update(movement, serializer.validated_data)
        except DjangoValidationError as exc:
            return Response(
                {"error": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response = StockMovementSerializer(updated)
        return Response({"data": response.data}, status=status.HTTP_200_OK)
