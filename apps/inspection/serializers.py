from rest_framework import serializers

from apps.inspection.models import Inspection
from apps.inspection.validators import User, validate_responsible_is_auditor


class InspectionSerializer(serializers.ModelSerializer):
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
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
