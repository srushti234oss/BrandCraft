from rest_framework import serializers
from .models import Brand


class BrandSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Brand
        fields = (
            "id",
            "owner",
            "name",
            "industry",
            "description",
            "interview_data",
            "strategy_report",
            "strategy_data",
            "report_mode",
            "created_at",
        )
        read_only_fields = (
            "id",
            "owner",
            "interview_data",
            "strategy_report",
            "strategy_data",
            "report_mode",
            "created_at",
        )

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Brand name cannot be blank.")
        return value

    def validate_industry(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Industry cannot be blank.")
        return value

    def validate_description(self, value):
        if len(value.strip()) > 5_000:
            raise serializers.ValidationError("Description must be 5,000 characters or fewer.")
        return value.strip()
