from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.supply_lot.services import SupplyLotService
from apps.supply_lot.serializers import SupplyLotSerializer

class SupplyLotListAPIView(APIView):
    def get(self, request):
        supply_lots = SupplyLotService.list_all()
        serializer = SupplyLotSerializer(supply_lots, many = True)
        return Response({
            "data": serializer.data
        }, status = status.HTTP_200_OK)
    
    def post(self, request):
        serializer = SupplyLotSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        supply_lot = SupplyLotService.create(serializer.validated_data)
        response = SupplyLotSerializer(supply_lot)
        return Response({
            "data": response.data
        }, status = status.HTTP_201_CREATED)
    
class SupplyLotDetailAPIView(APIView):
    def get(self, request, pk):
        try: 
            supply_lot_model = SupplyLotService.get(pk)
            serializer = SupplyLotSerializer(supply_lot_model)
            return Response({
                "data": serializer.data
            }, status = status.HTTP_200_OK)
        except Http404:
            return Response({
                "error": "Supply Lot Not Found"
            }, status = status.HTTP_404_NOT_FOUND)
    
    def patch(self, request, pk):
        try:
            supply_lot = SupplyLotService.get(pk)
            serializer = SupplyLotSerializer(supply_lot, data = request.data, partial = True)
            serializer.is_valid(raise_exception = True)
            updated = SupplyLotService.update(instance = supply_lot, validated_data = serializer.validated_data)
            response = SupplyLotSerializer(updated)
            return Response({
                "data": response.data
            }, status = status.HTTP_200_OK)
        except Http404:
            return Response({
                "error": "Supply Lot Not Found"
            }, status = status.HTTP_404_NOT_FOUND)
        
    def delete(self, request, pk):
        try:
            SupplyLotService.delete(pk = pk)
            return Response(status = status.HTTP_204_NO_CONTENT)

        except Http404:
            return Response({
                "error": "Supply Lot Not Found"
            }, status = status.HTTP_404_NOT_FOUND)   
            
        

 