from django.db import transaction
from rest_framework import status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer
from .models import EmailVerificationCode, User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .utils import send_verification_email
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
import random
from hotel.models import Hotel
from hotel.serializers import HotelSerializer


class AuthViewSet(viewsets.ViewSet):
    """
    A viewset for handling authentication related actions.
    """

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={
            201: openapi.Response('User created successfully', UserSerializer),
            400: 'Bad Request'
        },
        operation_description="Register a new user account.",
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        data = request.data
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            with transaction.atomic():
                user = User.objects.create_user(
                    email=validated_data['email'],
                    name=validated_data['name'],
                    last_name=validated_data['last_name'],
                    role='Customer',
                    password=validated_data['password'],
                    is_active=False  # User won't be active until email is verified
                )
                verification = EmailVerificationCode.objects.create(user=user)
                send_verification_email(user, verification)
            return Response({
                'user': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'password': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['email', 'password']
        ),
        responses={
            200: openapi.Response('Login successful', UserSerializer),
            401: 'Invalid credentials'
        },
        operation_description="Authenticate a user and return JWT tokens.",
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            user = User.objects.get(email=email)

            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)


    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={
            200: openapi.Response(
                description="Email verified successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: 'Bad Request'
        },
        operation_description="Verify user's email using the verification code.",
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='verify-email')
    def verify_email(self, request):
        try:
            email = request.data['email']
            verification_code = request.data['verification_code']
            verification = EmailVerificationCode.objects.get(user__email=email)
            user = verification.user
            if verification.code == verification_code:
                with transaction.atomic():
                    user.is_active = True
                    user.save()
                    verification.is_verified = True
                    verification.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    "status": "success",
                    "message": UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }, status=status.HTTP_200_OK)
            return Response({'error': 'code error'}, status=status.HTTP_400_BAD_REQUEST)
        except EmailVerificationCode.DoesNotExist:
            return Response({'error': 'code does not exist'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={
            200: openapi.Response(
                description="New verification code sent",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: 'Bad Request'
        },
        operation_description="Resend email verification code to the user's email.",
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='resend-verification-code')
    def resend_verification_code(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            with transaction.atomic():
                EmailVerificationCode.objects.filter(user=user).delete()
                verification = EmailVerificationCode.objects.create(user=user)
                send_verification_email(user, verification)

            return Response({
                "status": "success",
                "message": "A new verification code has been sent to your email."
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def forgot_password(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate a 6-digit verification code
        verification_code = str(random.randint(100000, 999999))
        
        # Store in cache with 10-minute expiration (600 seconds)
        cache.set(f'password_reset_{email}', verification_code, timeout=600)
        
        # Send email with verification code
        try:
            send_mail(
                'Password Reset Verification Code',
                f'Your verification code is: {verification_code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return Response({'message': 'Verification code sent to email'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        email = request.data.get('email')
        verification_code = request.data.get('verification_code')
        new_password = request.data.get('new_password')
        
        if not all([email, verification_code, new_password]):
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get cached code
        cached_code = cache.get(f'password_reset_{email}')
        
        if not cached_code or cached_code != verification_code:
            return Response({'error': 'Invalid or expired verification code'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find user and set new password
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            # Delete the verification code from cache
            cache.delete(f'password_reset_{email}')
            
            return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class UserViewSet(viewsets.ViewSet):
    """
    A viewset for handling user profile related actions.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: openapi.Response('User profile retrieved successfully', UserSerializer)
        },
        operation_description="Get the authenticated user's profile.",
        tags=['User']
    )
    @action(detail=False, methods=['get'], url_path='profile')
    def profile(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={
            200: openapi.Response('User profile updated successfully', UserSerializer),
            400: 'Bad Request'
        },
        operation_description="Update the authenticated user's profile.",
        tags=['User']
    )
    @action(detail=False, methods=['put'], url_path='profile')
    def update_profile(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['refresh']
        ),
        responses={
            205: 'Logout successful',
            400: 'Invalid token'
        },
        operation_description="Logout the user by blacklisting the refresh token.",
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(
                {"error": e},
                status=status.HTTP_400_BAD_REQUEST
            )


class FavoriteHotelsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'hotel_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Hotel ID to add to favorites'),
            },
            required=['hotel_id']
        ),
        responses={
            201: openapi.Response(
                description="Hotel added to favorites successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'hotel': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: 'Bad Request - Hotel already in favorites or invalid hotel ID',
            404: 'Hotel not found'
        },
        operation_description="Add a hotel to the user's favorite list.",
        tags=['Favorites']
    )
    @action(detail=False, methods=['post'], url_path='add')
    def add_to_favorites(self, request):
        try:
            hotel_id = request.data.get('hotel_id')
            if not hotel_id:
                return Response({'error': 'Hotel ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            hotel = get_object_or_404(Hotel, id=hotel_id, status="Accepted")
            
            if request.user.favorite_hotels.filter(id=hotel_id).exists():
                return Response({'error': 'Hotel is already in your favorites'}, status=status.HTTP_400_BAD_REQUEST)
            
            request.user.favorite_hotels.add(hotel)
            
            serializer = HotelSerializer(hotel, context={'request': request})
            return Response({
                'message': 'Hotel added to favorites successfully',
                'hotel': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={
            200: openapi.Response('User favorite hotels retrieved successfully', HotelSerializer(many=True)),
            404: 'No favorite hotels found'
        },
        operation_description="Get all favorite hotels for the authenticated user.",
        tags=['Favorites']
    )
    @action(detail=False, methods=['get'], url_path='list')
    def get_favorites(self, request):
        favorite_hotels = request.user.favorite_hotels.filter(status="Accepted").select_related('hotel_manager').prefetch_related('facilities', 'rooms')
        
        if not favorite_hotels.exists():
            return Response({'message': 'No favorite hotels found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = HotelSerializer(favorite_hotels, many=True, context={'request': request})
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'hotel_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Hotel ID to remove from favorites'),
            },
            required=['hotel_id']
        ),
        responses={
            200: openapi.Response(
                description="Hotel removed from favorites successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: 'Bad Request - Hotel not in favorites',
            404: 'Hotel not found'
        },
        operation_description="Remove a hotel from the user's favorite list.",
        tags=['Favorites']
    )
    @action(detail=False, methods=['delete'], url_path='remove')
    def remove_from_favorites(self, request):
        try:
            hotel_id = request.data.get('hotel_id')
            if not hotel_id:
                return Response({'error': 'Hotel ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            hotel = get_object_or_404(Hotel, id=hotel_id)
            
            if not request.user.favorite_hotels.filter(id=hotel_id).exists():
                return Response({'error': 'Hotel is not in your favorites'}, status=status.HTTP_400_BAD_REQUEST)
            
            request.user.favorite_hotels.remove(hotel)
            
            return Response({
                'message': 'Hotel removed from favorites successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('hotel_id', openapi.IN_PATH, description="Hotel ID", type=openapi.TYPE_INTEGER)
        ],
        responses={
            200: openapi.Response(
                description="Favorite status retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'is_favorite': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                    }
                )
            ),
            404: 'Hotel not found'
        },
        operation_description="Check if a hotel is in the user's favorites.",
        tags=['Favorites']
    )
    @action(detail=True, methods=['get'], url_path='is-favorite')
    def is_favorite(self, request, pk=None):
        hotel = get_object_or_404(Hotel, id=pk)
        is_favorite = request.user.favorite_hotels.filter(id=pk).exists()
        
        return Response({
            'is_favorite': is_favorite
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Favorites cleared successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        },
        operation_description="Clear all favorite hotels for the authenticated user.",
        tags=['Favorites']
    )
    @action(detail=False, methods=['delete'], url_path='clear-all')
    def clear_favorites(self, request):
        request.user.favorite_hotels.clear()
        
        return Response({
            'message': 'All favorite hotels cleared successfully'
        }, status=status.HTTP_200_OK)