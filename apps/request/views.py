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
from apps.request.serializers import RequestSerializer
from apps.request.services import RequestServices

RequestEnvelopeSerializer = inline_serializer(
    name="RequestEnvelope",
    fields={"data": RequestSerializer()},
)

RequestListEnvelopeSerializer = inline_serializer(
    name="RequestListEnvelope",
    fields={"data": RequestSerializer(many=True)},
)

ErrorResponseSerializer = inline_serializer(
    name="RequestErrorResponse",
    fields={"error": serializers.CharField()},
)

@extend_schema(tags=["requests"])
@extend_schema_view(
    get=extend_schema(
        operation_id="requests_list",
        summary="List requests",
        description="Returns all requests. Requires authentication.",
        responses={200: RequestListEnvelopeSerializer},
    ),
    post=extend_schema(
        operation_id="requests_create",
        summary="Create request",
        description="Creates a new request. Requires authentication.",
        request=RequestSerializer,
        responses={
            201: RequestEnvelopeSerializer,
            400: OpenApiResponse(
                description="Validation error."
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
    ),
)
class RequestListAPIView(APIView):
    serializer_class = RequestSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests = RequestServices.list_all()
        serializer = RequestSerializer(requests, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request_obj = RequestServices.create(serializer.validated_data)
        response = RequestSerializer(request_obj)
        return Response({"data": response.data}, status=status.HTTP_201_CREATED)
    

@extend_schema(tags=["requests"])
@extend_schema_view(
    get=extend_schema(
        operation_id="requests_retrieve",
        summary="Retrieve request",
        description="Returns a single request by ID.",
        responses={
            200: RequestEnvelopeSerializer,
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Request not found.",
            ),
        },
    ),
    patch=extend_schema(
        operation_id="requests_partial_update",
        summary="Partially update request",
        description="Updates a request. Requires authentication.",
        request=RequestSerializer,
        responses={
            200: RequestEnvelopeSerializer,
            400: OpenApiResponse(
                description="Validation error."
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Request not found.",
            ),
        },
    ),
    delete=extend_schema(
        operation_id="requests_destroy",
        summary="Delete request",
        description="Deletes a request. Requires authentication.",
        responses={
            204: OpenApiResponse(
                description="Request deleted."
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Request not found.",
            ),
        },
    ),
)
class RequestDetailAPIView(APIView):
    serializer_class = RequestSerializer
    permission_classes = [IsAuthenticated]


    def get(self, request, pk):
        try:
            request_obj = RequestServices.get(pk)
        except Http404:
            return Response(
                {"error": "Request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RequestSerializer(request_obj)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        try:
            request_obj = RequestServices.get(pk)
        except Http404:
            return Response(
                {"error": "Request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RequestSerializer(
            request_obj, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        updated = RequestServices.update(request_obj, serializer.validated_data)
        response = RequestSerializer(updated)
        return Response({"data": response.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            RequestServices.delete(pk)
        except Http404:
            return Response(
                {"error": "Request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

