import logging

from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from brands.models import Brand
from .serializers import (
    AudienceShiftSerializer,
    ConsistencyReviewSerializer,
    DirectionSelectionSerializer,
    InterviewRequestSerializer,
    LoginSerializer,
    RegistrationSerializer,
    ReportRequestSerializer,
)
from .services import (
    AIServiceError,
    check_brand_consistency,
    generate_audience_variants,
    generate_brand_strategy,
    generate_interview_question,
    get_ai_mode,
)

logger = logging.getLogger(__name__)


def _owned_brand_or_404(request, brand_id):
    return get_object_or_404(Brand, id=brand_id, owner=request.user)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_interview(request):
    serializer = InterviewRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    brand = _owned_brand_or_404(request, serializer.validated_data["brand_id"])
    answer = serializer.validated_data.get("answer", "")
    history = list(brand.interview_data or [])

    if history and not history[-1].get("answer") and not answer:
        return Response(
            {
                "brand_id": brand.id,
                "question": history[-1]["question"],
                "history": history,
                "complete": False,
                "mode": get_ai_mode(),
                "progress": {"completed": sum(bool(item.get("answer")) for item in history), "total": 6},
            },
            status=status.HTTP_200_OK,
        )

    if answer:
        if not history or history[-1].get("answer"):
            return Response(
                {"error": "Start the interview before submitting an answer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        history[-1]["answer"] = answer

    try:
        result = generate_interview_question(
            brand.name, brand.industry, brand.description, history
        )
    except AIServiceError as error:
        return Response({"error": str(error)}, status=error.status_code)
    except Exception:
        logger.exception("Unexpected interview generation failure")
        return Response(
            {"error": "The interview could not continue right now. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if result["question"]:
        history.append({"question": result["question"], "answer": ""})

    brand.interview_data = history
    brand.save(update_fields=["interview_data"])
    return Response(
        {
            "brand_id": brand.id,
            "question": result["question"],
            "history": history,
            "complete": result["complete"],
            "mode": result["mode"],
            "progress": {"completed": sum(bool(item.get("answer")) for item in history), "total": 6},
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_report(request):
    serializer = ReportRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    brand = _owned_brand_or_404(request, serializer.validated_data["brand_id"])

    if not brand.interview_data:
        return Response(
            {"error": "Start the founder interview before generating a report."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = generate_brand_strategy(
            brand.name, brand.industry, brand.description, brand.interview_data
        )
    except AIServiceError as error:
        return Response({"error": str(error)}, status=error.status_code)
    except Exception:
        logger.exception("Unexpected report generation failure")
        return Response(
            {"error": "The strategy report could not be generated right now. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    brand.strategy_report = result["report"]
    brand.strategy_data = result["strategy_data"]
    brand.report_mode = result["mode"]
    brand.save(update_fields=["strategy_report", "strategy_data", "report_mode"])
    return Response(
        {
            "brand_id": brand.id,
            "brand_name": brand.name,
            "report": result["report"],
            "strategy_data": result["strategy_data"],
            "mode": result["mode"],
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_saved_report(request, brand_id):
    brand = _owned_brand_or_404(request, brand_id)
    if not brand.strategy_report:
        return Response(
            {"error": "A strategy report has not been generated for this brand yet."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(
        {
            "brand_id": brand.id,
            "brand_name": brand.name,
            "report": brand.strategy_report,
            "strategy_data": brand.strategy_data,
            "mode": brand.report_mode,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def select_direction(request):
    serializer = DirectionSelectionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    brand = _owned_brand_or_404(request, serializer.validated_data["brand_id"])
    data = dict(brand.strategy_data or {})
    direction = next(
        (item for item in data.get("directions", []) if item.get("id") == serializer.validated_data["direction_id"]),
        None,
    )
    if not direction:
        return Response({"error": "Generate the brand strategy before selecting a direction."}, status=status.HTTP_400_BAD_REQUEST)

    data["selected_direction_id"] = direction["id"]
    data["selected_direction"] = direction
    data["positioning"] = direction["positioning"]
    data["audience"] = direction["audience"]
    data["personality"] = direction["personality"]
    data["voice"] = direction["voice"]
    data["taglines"] = [direction["tagline"]]
    data["visual_direction"] = direction["visual_direction"]
    data["launch_kit"] = direction["launch_kit"]
    brand.strategy_data = data
    brand.save(update_fields=["strategy_data"])
    return Response({"strategy_data": data}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def shift_audience(request):
    serializer = AudienceShiftSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    brand = _owned_brand_or_404(request, serializer.validated_data["brand_id"])
    data = dict(brand.strategy_data or {})
    if not data:
        return Response({"error": "Generate the brand strategy before shifting audiences."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        variants = generate_audience_variants(brand, data, serializer.validated_data["audiences"])
    except AIServiceError as error:
        return Response({"error": str(error)}, status=error.status_code)
    except Exception:
        logger.exception("Unexpected audience-shift failure")
        return Response({"error": "Audience variants could not be created right now."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    data["audience_variants"] = variants
    brand.strategy_data = data
    brand.save(update_fields=["strategy_data"])
    return Response({"variants": variants}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def review_content(request):
    serializer = ConsistencyReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    brand = _owned_brand_or_404(request, serializer.validated_data["brand_id"])
    data = dict(brand.strategy_data or {})
    if not data:
        return Response({"error": "Generate the brand strategy before checking content."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        review = check_brand_consistency(brand, data, serializer.validated_data["content"])
    except AIServiceError as error:
        return Response({"error": str(error)}, status=error.status_code)
    except Exception:
        logger.exception("Unexpected brand-consistency review failure")
        return Response({"error": "This content could not be checked right now."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    data["consistency_check"] = review
    brand.strategy_data = data
    brand.save(update_fields=["strategy_data"])
    return Response(review, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([])
def register_user(request):
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {
            "message": "User registered successfully.",
            "username": user.username,
            "token": token.key,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([])
def login_user(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        username=serializer.validated_data["username"],
        password=serializer.validated_data["password"],
    )
    if user is None:
        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {"message": "Login successful.", "username": user.username, "token": token.key},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_user(request):
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response({"username": request.user.username}, status=status.HTTP_200_OK)
