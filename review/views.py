from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer
from hotel.models import Hotel
from accounts.models import User

def update_hotel_rating(hotel):
    """Update hotel rating based on all reviews"""
    reviews = Review.objects.filter(hotel=hotel)
    if reviews.exists():
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
        hotel.rate = round(avg_rating)
        hotel.rate_number = reviews.count()
    else:
        hotel.rate = 0
        hotel.rate_number = 0
    hotel.save()

@swagger_auto_schema(
    method='get',
    operation_description="Get all reviews for a specific hotel",
    responses={200: ReviewSerializer(many=True), 404: 'Hotel not found'}
)
@swagger_auto_schema(
    method='post',
    operation_description="Create or update a review for a hotel. Only customers can create reviews.",
    request_body=ReviewCreateSerializer,
    responses={
        201: ReviewSerializer,
        400: 'Bad request - validation errors',
        403: 'Only customers can create reviews',
        404: 'Hotel not found'
    }
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def review_list_create(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    user = request.user

    if request.method == 'GET':
        reviews = Review.objects.filter(hotel=hotel)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        if user.role != 'Customer':
            return Response({'error': 'Only customers can create reviews'}, status=status.HTTP_403_FORBIDDEN)

        existing_review = Review.objects.filter(user=user, hotel=hotel).first()

        with transaction.atomic():
            if existing_review:
                serializer = ReviewCreateSerializer(existing_review, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    response_serializer = ReviewSerializer(existing_review)
                    update_hotel_rating(hotel)
                    return Response(response_serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer = ReviewCreateSerializer(data=request.data)
                if serializer.is_valid():
                    review = serializer.save(user=user, hotel=hotel)
                    response_serializer = ReviewSerializer(review)
                    update_hotel_rating(hotel)
                    return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    operation_description="Get a specific review by ID",
    responses={200: ReviewSerializer, 403: 'Only customers can access reviews', 404: 'Review not found'}
)
@swagger_auto_schema(
    method='put',
    operation_description="Update a specific review",
    request_body=ReviewCreateSerializer,
    responses={200: ReviewSerializer, 400: 'Bad request', 403: 'Only customers can update reviews', 404: 'Not found'}
)
@swagger_auto_schema(
    method='patch',
    operation_description="Partially update a specific review",
    request_body=ReviewCreateSerializer,
    responses={200: ReviewSerializer, 400: 'Bad request', 403: 'Only customers can update reviews', 404: 'Not found'}
)
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a specific review",
    responses={204: 'Deleted successfully', 403: 'Only customers can delete reviews', 404: 'Not found'}
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def review_detail(request, pk):
    user = request.user
    if user.role != 'Customer':
        return Response({'error': 'Only customers can access reviews'}, status=status.HTTP_403_FORBIDDEN)

    review = get_object_or_404(Review, pk=pk, user=user)

    if request.method == 'GET':
        serializer = ReviewSerializer(review)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ReviewCreateSerializer(review, data=request.data, partial=partial)
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
                response_serializer = ReviewSerializer(review)
                update_hotel_rating(review.hotel)
                return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        with transaction.atomic():
            hotel = review.hotel
            review.delete()
            update_hotel_rating(hotel)
            return Response(status=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(
    method='get',
    operation_description="Get review stats for a hotel (average, total, distribution)",
    responses={
        200: openapi.Response(
            description="Hotel review stats",
            examples={
                "application/json": {
                    "hotel_id": 1,
                    "hotel_name": "Hotel X",
                    "average_rating": 4.3,
                    "total_reviews": 15,
                    "rating_distribution": {
                        "rating_1": 1,
                        "rating_2": 2,
                        "rating_3": 3,
                        "rating_4": 4,
                        "rating_5": 5
                    }
                }
            }
        ),
        404: 'Hotel not found'
    }
)
@api_view(['GET'])
def hotel_review_stats(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)

    stats = Review.objects.filter(hotel=hotel).aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id')
    )

    rating_distribution = {
        f'rating_{i}': Review.objects.filter(hotel=hotel, rating=i).count()
        for i in range(1, 6)
    }

    return Response({
        'hotel_id': hotel_id,
        'hotel_name': hotel.name,
        'average_rating': round(stats['avg_rating'] or 0, 1),
        'total_reviews': stats['total_reviews'],
        'rating_distribution': rating_distribution
    })

@swagger_auto_schema(
    method='get',
    operation_description="Get the current customer's review for a specific hotel",
    responses={200: ReviewSerializer, 403: 'Only customers can access reviews', 404: 'Review not found'}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_hotel_review(request, hotel_id):
    user = request.user
    if user.role != 'Customer':
        return Response({'error': 'Only customers can access reviews'}, status=status.HTTP_403_FORBIDDEN)

    try:
        review = Review.objects.get(user=user, hotel_id=hotel_id)
        serializer = ReviewSerializer(review)
        return Response(serializer.data)
    except Review.DoesNotExist:
        return Response({'detail': 'No review found'}, status=status.HTTP_404_NOT_FOUND)
