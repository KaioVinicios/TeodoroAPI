from django.http import Http404
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
    OpenApiExample,
    OpenApiResponse,
)

from apps.account.services import AccountServices
from apps.account.permissions import IsNotCustomer
from apps.account.serializers import AccountSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated


AccountEnvelopeSerializer = inline_serializer(
    name="AccountEnvelope",
    fields={"data": AccountSerializer()},
)

AccountListEnvelopeSerializer = inline_serializer(
    name="AccountListEnvelope",
    fields={"data": AccountSerializer(many=True)},
)

ErrorResponseSerializer = inline_serializer(
    name="AccountErrorResponse",
    fields={"error": serializers.CharField()},
)


@extend_schema(tags=["accounts"])
@extend_schema_view(
    get=extend_schema(
        operation_id="accounts_list",
        summary="List accounts",
        description=(
            "Returns every account registered in the system, wrapped in a "
            "`data` envelope. Requires an authenticated non-customer user "
            "(e.g. admin)."
        ),
        responses={
            200: AccountListEnvelopeSerializer,
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(
                description="Authenticated user is a customer and cannot list accounts."
            ),
        },
    ),
    post=extend_schema(
        operation_id="accounts_create",
        summary="Create account (sign up)",
        description=(
            "Creates a new `User` + `Account` pair atomically. This endpoint "
            "is open to anonymous clients so that new users can register."
        ),
        request=AccountSerializer,
        responses={
            201: AccountEnvelopeSerializer,
            400: OpenApiResponse(
                description="Validation error (invalid CPF, duplicated username, etc.)."
            ),
        },
        examples=[
            OpenApiExample(
                "Valid signup payload",
                value={
                    "username": "joao",
                    "password": "StrongPass!23",
                    "email": "joao@example.com",
                    "first_name": "Joao",
                    "last_name": "Silva",
                    "account_type": "customer",
                    "cpf": "529.982.247-25",
                    "address": "Rua das Flores, 10",
                    "phone_number": "(11) 91234-5678",
                    "organization": None,
                },
                request_only=True,
            ),
        ],
    ),
)
class AccountListAPIView(APIView):
    serializer_class = AccountSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAuthenticated(), IsNotCustomer()]

    def get(self, request):
        accounts = AccountServices.list_all()
        serializer = AccountSerializer(accounts, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account = AccountServices.create(serializer.validated_data)
        response = AccountSerializer(account)
        return Response({"data": response.data}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["accounts"])
@extend_schema_view(
    get=extend_schema(
        operation_id="accounts_retrieve",
        summary="Retrieve account",
        description="Returns a single account identified by its primary key.",
        responses={
            200: AccountEnvelopeSerializer,
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Account not found.",
            ),
        },
    ),
    patch=extend_schema(
        operation_id="accounts_partial_update",
        summary="Partially update account",
        description=(
            "Updates any subset of fields on the underlying `User` and "
            "`Account`. When `password` is supplied it is re-hashed before "
            "being stored."
        ),
        request=AccountSerializer,
        responses={
            200: AccountEnvelopeSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Account not found.",
            ),
        },
    ),
    delete=extend_schema(
        operation_id="accounts_destroy",
        summary="Delete account",
        description=(
            "Hard-deletes the account and cascades the removal to its linked "
            "`User`. Restricted to authenticated non-customer users."
        ),
        responses={
            204: OpenApiResponse(description="Account deleted."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(
                description="Authenticated user is a customer and cannot delete accounts."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Account not found.",
            ),
        },
    ),
)
class AccountDetailAPIView(APIView):
    serializer_class = AccountSerializer

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsNotCustomer()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        try:
            account = AccountServices.get(pk)
        except Http404:
            return Response(
                {"error": "Account not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AccountSerializer(account)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        try:
            account = AccountServices.get(pk)
        except Http404:
            return Response(
                {"error": "Account not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AccountSerializer(account, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated = AccountServices.update(account, serializer.validated_data)
        response = AccountSerializer(updated)
        return Response({"data": response.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            AccountServices.delete(pk)
        except Http404:
            return Response(
                {"error": "Account not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
