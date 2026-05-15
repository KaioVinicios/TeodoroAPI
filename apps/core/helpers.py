from rest_framework import status as drf_status
from rest_framework.response import Response


def api_response(
    status: int = drf_status.HTTP_200_OK,
    title: str = "",
    message: str = "",
    description: str = "",
    data: dict = {},
    errors: dict = {},
) -> Response:
    return Response(
        {
            "title": title,
            "message": message,
            "description": description,
            "data": data,
            "errors": errors,
        },
        status=status,
    )
