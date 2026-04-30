from django.http import Http404
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
    OpenApiResponse,
)
from apps.supply_lot.services import SupplyLotService
from apps.supply_lot.serializers import SupplyLotSerializer


SupplyLotEnvelopeSerializer = inline_serializer(
    name="SupplyLotEnvelope",
    fields={"data": SupplyLotSerializer()},
)

SupplyLotListEnvelopeSerializer = inline_serializer(
    name="SupplyLotListEnvelope",
    fields={"data": SupplyLotSerializer(many=True)},
)

ErrorResponseSerializer = inline_serializer(
    name="SupplyLotErrorResponse",
    fields={"error": serializers.CharField()},
)


@extend_schema(tags=["supply-lots"])
@extend_schema_view(
    get=extend_schema(
        operation_id="supply_lots_list",
        summary="List supply lots",
        description="Returns all supply lots. Requires authentication.",
        responses={
            200: SupplyLotListEnvelopeSerializer,
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
    ),
    post=extend_schema(
        operation_id="supply_lots_create",
        summary="Create supply lot",
        description="Creates a new supply lot. Requires authentication.",
        request=SupplyLotSerializer,
        responses={
            201: SupplyLotEnvelopeSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
    ),
)
class SupplyLotListAPIView(APIView):
    serializer_class = SupplyLotSerializer

    def get(self, request):
        supply_lots = SupplyLotService.list_all()
        serializer = SupplyLotSerializer(supply_lots, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SupplyLotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supply_lot = SupplyLotService.create(serializer.validated_data)
        response = SupplyLotSerializer(supply_lot)
        return Response({"data": response.data}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["supply-lots"])
@extend_schema_view(
    get=extend_schema(
        operation_id="supply_lots_retrieve",
        summary="Retrieve supply lot",
        description="Returns a single supply lot by ID.",
        responses={
            200: SupplyLotEnvelopeSerializer,
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Supply lot not found.",
            ),
        },
    ),
    patch=extend_schema(
        operation_id="supply_lots_partial_update",
        summary="Partially update supply lot",
        description="Updates a supply lot. Requires authentication.",
        request=SupplyLotSerializer,
        responses={
            200: SupplyLotEnvelopeSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Supply lot not found.",
            ),
        },
    ),
    delete=extend_schema(
        operation_id="supply_lots_destroy",
        summary="Delete supply lot",
        description="Deletes a supply lot. Requires authentication.",
        responses={
            204: OpenApiResponse(description="Supply lot deleted."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Supply lot not found.",
            ),
        },
    ),
)
class SupplyLotDetailAPIView(APIView):
    serializer_class = SupplyLotSerializer

    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            return Response(
                {"error": "SupplyLot não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return super().handle_exception(exc)

    def get(self, request, pk):
        supply_lot_model = SupplyLotService.get(pk)
        serializer = SupplyLotSerializer(supply_lot_model)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        supply_lot = SupplyLotService.get(pk)
        serializer = SupplyLotSerializer(
            supply_lot, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated = SupplyLotService.update(
            instance=supply_lot, validated_data=serializer.validated_data
        )
        response = SupplyLotSerializer(updated)
        return Response({"data": response.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        SupplyLotService.delete(pk=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
