from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_username(self, value):
        if not value:
            raise serializers.ValidationError("Username cannot be blank.")
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_password(self, value):
        candidate = User(username=self.initial_data.get("username", ""))
        validate_password(value, user=candidate)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class InterviewRequestSerializer(serializers.Serializer):
    brand_id = serializers.IntegerField(min_value=1)
    answer = serializers.CharField(required=False, allow_blank=True, max_length=2_000, trim_whitespace=True)


class ReportRequestSerializer(serializers.Serializer):
    brand_id = serializers.IntegerField(min_value=1)


class DirectionSelectionSerializer(serializers.Serializer):
    brand_id = serializers.IntegerField(min_value=1)
    direction_id = serializers.ChoiceField(choices=("premium", "everyday", "proof"))


class AudienceShiftSerializer(serializers.Serializer):
    brand_id = serializers.IntegerField(min_value=1)
    audiences = serializers.ListField(
        child=serializers.CharField(max_length=140, trim_whitespace=True),
        min_length=2,
        max_length=3,
    )

    def validate_audiences(self, values):
        cleaned = [value.strip() for value in values if value.strip()]
        if len(cleaned) < 2:
            raise serializers.ValidationError("Enter at least two audience segments to compare.")
        return cleaned


class ConsistencyReviewSerializer(serializers.Serializer):
    brand_id = serializers.IntegerField(min_value=1)
    content = serializers.CharField(max_length=5_000, trim_whitespace=True)
