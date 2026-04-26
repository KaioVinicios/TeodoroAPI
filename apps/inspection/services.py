from apps.inspection.models import Inspection
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class InspectionServices:
    @staticmethod
    def list_all():
        return Inspection.objects.select_related("responsible").all()

    @staticmethod
    def get(pk):
        return get_object_or_404(
            Inspection.objects.select_related("responsible"), pk=pk
        )

    @staticmethod
    @transaction.atomic
    def create(validated_data):
        inspection = Inspection(**dict(validated_data))
        inspection.full_clean()

        inspection.is_complete = False
        inspection.completion_date = None

        inspection.save()
        return inspection

    @staticmethod
    @transaction.atomic
    def update(instance, validated_data):
        if instance.is_complete:
            raise ValidationError(
                _("Cannot update an inspection that is already complete.")
            )

        for attr, value in dict(validated_data).items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance

    @staticmethod
    @transaction.atomic
    def delete(pk):
        inspection = get_object_or_404(Inspection, pk=pk)
        inspection.delete()
