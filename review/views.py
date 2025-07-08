from rest_framework import generics, status
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
from accounts.models import Customer

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

class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        hotel_id = self.kwargs.get('hotel_id')
        return Review.objects.filter(hotel_id=hotel_id)
    
    @swagger_auto_schema(
        operation_description="Get all reviews for a specific hotel",
        responses={
            200: ReviewSerializer(many=True),
            404: 'Hotel not found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create or update a review for a hotel. Only customers can create reviews.",
        request_body=ReviewCreateSerializer,
        responses={
            201: ReviewSerializer,
            400: 'Bad request - validation errors',
            403: 'Only customers can create reviews',
            404: 'Hotel not found'
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    @transaction.atomic
    def perform_create(self, serializer):
        hotel_id = self.kwargs.get('hotel_id')
        hotel = get_object_or_404(Hotel, id=hotel_id)
        
        # Get the customer profile for the current user
        try:
            customer = Customer.objects.get(user=self.request.user)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Only customers can create reviews'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if customer already reviewed this hotel
        existing_review = Review.objects.filter(
            customer=customer, 
            hotel=hotel
        ).first()
        
        if existing_review:
            # Update existing review
            serializer.update(existing_review, serializer.validated_data)
        else:
            # Create new review
            serializer.save(customer=customer, hotel=hotel)
        
        # Update hotel rating
        update_hotel_rating(hotel)

class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only allow customers to access their own reviews
        try:
            customer = Customer.objects.get(user=self.request.user)
            return Review.objects.filter(customer=customer)
        except Customer.DoesNotExist:
            return Review.objects.none()
    
    @swagger_auto_schema(
        operation_description="Get a specific review by ID",
        responses={
            200: ReviewSerializer,
            403: 'Only customers can access reviews',
            404: 'Review not found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update a specific review",
        request_body=ReviewCreateSerializer,
        responses={
            200: ReviewSerializer,
            400: 'Bad request - validation errors',
            403: 'Only customers can update reviews',
            404: 'Review not found'
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Partially update a specific review",
        request_body=ReviewCreateSerializer,
        responses={
            200: ReviewSerializer,
            400: 'Bad request - validation errors',
            403: 'Only customers can update reviews',
            404: 'Review not found'
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete a specific review",
        responses={
            204: 'Review deleted successfully',
            403: 'Only customers can delete reviews',
            404: 'Review not found'
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    @transaction.atomic
    def perform_update(self, serializer):
        review = serializer.save()
        # Update hotel rating after review update
        update_hotel_rating(review.hotel)
    
    @transaction.atomic
    def perform_destroy(self, instance):
        hotel = instance.hotel
        instance.delete()
        # Update hotel rating after review deletion
        update_hotel_rating(hotel)

@swagger_auto_schema(
    method='get',
    operation_description="Get comprehensive statistics for a hotel's reviews including average rating, total reviews, and rating distribution",
    responses={
        200: openapi.Response(
            description="Hotel review statistics",
            examples={
                "application/json": {
                    "hotel_id": 1,
                    "hotel_name": "Grand Hotel",
                    "average_rating": 4.2,
                    "total_reviews": 25,
                    "rating_distribution": {
                        "rating_1": 1,
                        "rating_2": 2,
                        "rating_3": 3,
                        "rating_4": 8,
                        "rating_5": 11
                    }
                }
            }
        ),
        404: 'Hotel not found'
    }
)
@api_view(['GET'])
def hotel_review_stats(request, hotel_id):
    """Get hotel review statistics"""
    hotel = get_object_or_404(Hotel, id=hotel_id)
    
    stats = Review.objects.filter(hotel=hotel).aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id')
    )
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[f'rating_{i}'] = Review.objects.filter(
            hotel=hotel, rating=i
        ).count()
    
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
    responses={
        200: ReviewSerializer,
        403: 'Only customers can have reviews',
        404: 'No review found for this hotel'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_hotel_review(request, hotel_id):
    """Get current customer's review for a specific hotel"""
    try:
        customer = Customer.objects.get(user=request.user)
        review = Review.objects.get(customer=customer, hotel_id=hotel_id)
        serializer = ReviewSerializer(review)
        return Response(serializer.data)
    except Customer.DoesNotExist:
        return Response({'error': 'Only customers can have reviews'}, status=status.HTTP_403_FORBIDDEN)
    except Review.DoesNotExist:
        return Response({'detail': 'No review found'}, status=status.HTTP_404_NOT_FOUND)