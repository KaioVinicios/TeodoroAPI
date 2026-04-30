from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.request.models import Request


class RequestServices:

    @staticmethod
    def list_all():
        return Request.objects.select_related("user", "supply").all()

    @staticmethod
    def get(pk):
        return get_object_or_404(
            Request.objects.select_related("user", "supply"),
            pk=pk,
        )

    @staticmethod
    @transaction.atomic
    def create(validated_data):
        request = Request(**dict(validated_data))
        request.full_clean()
        request.save()
        return request

    @staticmethod
    @transaction.atomic
    def update(instance, validated_data):
        for attr, value in dict(validated_data).items():
            setattr(instance, attr, value)

        instance.full_clean()
        instance.save()
        return instance

    @staticmethod
    @transaction.atomic
    def delete(pk):
        request = get_object_or_404(Request, pk=pk)
        request.delete()