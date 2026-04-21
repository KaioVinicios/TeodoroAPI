from rest_framework import serializers

from apps.inspection.models import Inspection
from apps.inspection.validators import User, validate_responsible_is_auditor


class InspectionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    responsible = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=False,
        required=True,
    )

    def validate_responsible(self, value):
        validate_responsible_is_auditor(value)
        return value

    class Meta:
        model = Inspection
        fields = [
            "id",
            "is_complete",
            "completion_date",
            "responsible",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
