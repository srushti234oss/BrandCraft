from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Brand
from .serializers import BrandSerializer


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def brand_collection(request):
    if request.method == "GET":
        brands = BrandSerializer(
            request.user.brands.order_by("-created_at"), many=True
        )
        return Response(brands.data, status=status.HTTP_200_OK)

    serializer = BrandSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(owner=request.user)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def brand_detail(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)

    if request.method == "GET":
        return Response(BrandSerializer(brand).data, status=status.HTTP_200_OK)

    if request.method in ("PUT", "PATCH"):
        serializer = BrandSerializer(
            brand,
            data=request.data,
            partial=request.method == "PATCH",
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    brand.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Keeps the original endpoint name and URL working for existing callers.
create_brand = brand_collection
