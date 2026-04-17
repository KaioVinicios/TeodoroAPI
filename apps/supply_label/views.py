from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.supply_label.services import SupplyLabelServices
from apps.supply_label.serializers import SupplyLabelSerializer


class SupplyLabelListAPIView(APIView):

    def get(self, request):
        supply_labels = SupplyLabelServices.list_all()
        serializer = SupplyLabelSerializer(supply_labels, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SupplyLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        supply_label = SupplyLabelServices.create(serializer.validated_data)
        response = SupplyLabelSerializer(supply_label)

        return Response({"data": response.data}, status=status.HTTP_201_CREATED)


class SupplyLabelDetailAPIView(APIView):

    def get(self, request, pk):
        try:
            supply_label_model = SupplyLabelServices.get(pk)
            serializer = SupplyLabelSerializer(supply_label_model)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)

        except Http404:
            return Response(
                {"error": "Supply Label not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request, pk):

        try:
            supply_label = SupplyLabelServices.get(pk=pk)
            serializer = SupplyLabelSerializer(
                supply_label, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)

            updated = SupplyLabelServices.update(
                instance=supply_label, validated_data=serializer.validated_data
            )
            response = SupplyLabelSerializer(updated)

            return Response({"data": response.data}, status=status.HTTP_200_OK)

        except Http404:
            return Response(
                {"error": "Supply Label not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, pk):
        try:
            SupplyLabelServices.delete(pk=pk)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Http404:
            return Response(
                {"error": "Supply Label not found"}, status=status.HTTP_404_NOT_FOUND
            )
