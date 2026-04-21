from django.http import Http404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.views import APIView, Response
from rest_framework.permissions import IsAuthenticated

from apps.inspection.permissions import isAuditor
from apps.inspection.serializers import InspectionSerializer
from apps.inspection.services import InspectionServices

InspectionEnvelopeSerializer = inline_serializer(
    name="InspectionEnvelope",
    fields={"data": InspectionSerializer()},
)

InspectionListEnvelopeSerializer = inline_serializer(
    name="InspectionListEnvelope",
    fields={"data": InspectionSerializer(many=True)},
)

ErrorResponseSerializer = inline_serializer(
    name="InspectionErrorResponse",
    fields={"error": serializers.CharField()},
)


@extend_schema(tags=["inspections"])
@extend_schema_view(
    get=extend_schema(
        operation_id="inspections_list",
        summary="List inspections",
        description=(
            "Returns every inspection registered in the system, wrapped in a "
            "`data` envelope. Requires an authenticated user."
        ),
        responses={
            200: InspectionListEnvelopeSerializer,
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(
                description="Authenticated user is not authorized to list accounts."
            ),
        },
    ),
    post=extend_schema(
        operation_id="inspections_create",
        summary="Create inspection",
        description=(
            "Creates a new `Inspection`. Restricted to authenticated auditors."
        ),
        request=InspectionSerializer,
        responses={
            201: InspectionEnvelopeSerializer,
            400: OpenApiResponse(
                description="Validation error (e.g. responsible user is not an auditor)."
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(
                description="Authenticated user is not authorized to create inspections."
            ),
        },
        examples=[
            OpenApiExample(
                "Valid request payload",
                value={
                    "responsible": 1,
                },
                request_only=True,
            )
        ],
    ),
)
class InspectionListAPIView(APIView):
    serializer_class = InspectionSerializer

    def get_permissions(self):
        return [IsAuthenticated(), isAuditor()]

    def get(self, request):
        inspections = InspectionServices.list_all()
        serializer = InspectionSerializer(inspections, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = InspectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        inspection = InspectionServices.create(serializer.validated_data)
        response_serializer = InspectionSerializer(inspection)
        return Response(
            {"data": response_serializer.data}, status=status.HTTP_201_CREATED
        )


@extend_schema(tags=["inspections"])
@extend_schema_view(
    get=extend_schema(
        operation_id="inspections_retrieve",
        summary="Retrieve inspection",
        description="Returns a single inspection identified by its primary key.",
        responses={
            200: InspectionEnvelopeSerializer,
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(
                description="Authenticated user is not authorized to retrieve inspections."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Inspection not found.",
            ),
        },
    ),
    patch=extend_schema(
        operation_id="inspections_partial_update",
        summary="Partially update inspection",
        description=(
            "Updates any subset of fields on the underlying `Inspection`. "
            "Restricted to authenticated auditors."
        ),
        request=InspectionSerializer,
        responses={
            200: InspectionEnvelopeSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(
                description="Authenticated user is not authorized to update inspections."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Inspection not found.",
            ),
        },
    ),
    delete=extend_schema(
        operation_id="inspections_destroy",
        summary="Delete inspection",
        description=(
            "Hard-deletes an existing `Inspection`. Restricted to authenticated auditors."
        ),
        responses={
            204: OpenApiResponse(description="Inspection deleted successfully."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(
                description="Authenticated user is not authorized to delete inspections."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Inspection not found.",
            ),
        },
    ),
)
class InspectionDetailAPIView(APIView):
    serializer_class = InspectionSerializer

    def get_permissions(self):
        return [IsAuthenticated(), isAuditor()]

    def get(self, request, pk):
        try:
            inspection = InspectionServices.get(pk)
        except Http404:
            return Response(
                {"error": "Inspection not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = InspectionSerializer(inspection)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        try:
            inspection = InspectionServices.get(pk)
        except Http404:
            return response(
                {"error": "Inspection not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = InspectionSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated = InspectionServices.update(inspection, serializer.validated_data)
        response = InspectionSerializer(updated)
        return Response({"data": response.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            InspectionServices.delete(pk)
        except Http404:
            return Response(
                {"error": "Inspection not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
