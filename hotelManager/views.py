from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import User, EmailVerificationCode
from accounts.serializers import UserSerializer
from hotelManager.models import HotelManager
from hotelManager.serializers import HotelManagerSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from accounts.utils import send_verification_email
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)


class HotelManagerViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get authenticated hotel manager's profile",
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            404: openapi.Response(
                description="Not Found",
                examples={
                    "application/json": {"error": "hotel manager not found"}
                }
            )
        }
    )
    def retrieve(self, request, pk=None):
        try:
            user_email = request.user.email
            hotel_manager = HotelManager.objects.get(user__email=user_email)
            serializer = HotelManagerSerializer(hotel_manager)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="List all hotel managers",
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            ),
            404: openapi.Response(
                description="Not Found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"error": "hotel manager not found"}
                }
            ),
            403: openapi.Response(
                description="Forbidden",
                examples={
                    "application/json": {"detail": "Authentication credentials were not provided."}
                }
            )
        }
    )
    def list(self, request):
        try:
            hotel_managers = HotelManager.objects.all()
            serializer = HotelManagerSerializer(hotel_managers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Update authenticated hotel manager's profile",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'national_code': openapi.Schema(type=openapi.TYPE_STRING),
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'errors': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            404: openapi.Response(
                description="Not Found",
                examples={
                    "application/json": {"error": "hotel manager not found"}
                }
            )
        }
    )
    def partial_update(self, request, pk=None):
        user_email = request.user.email
        try:
            hotel_manager = HotelManager.objects.get(user__email=user_email)
            data = request.data
            serializer = HotelManagerSerializer(data=data, instance=hotel_manager, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Delete hotel manager account",
        responses={
            204: openapi.Response(
                description="No Content",
            ),
            403: openapi.Response(
                description="Forbidden",
                examples={
                    "application/json": {"detail": "Authentication credentials were not provided."}
                }
            ),
            404: openapi.Response(
                description="Not Found",
                examples={
                    "application/json": {"error": "hotel manager not found"}
                }
            )
        }
    )
    def destroy(self, request, pk=None):
        try:
            user_email = request.user.email
            hotel_manager = HotelManager.objects.get(user__email=user_email)
            hotel_manager.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)


class NoneAuthHotelManagerViewSet(viewsets.ViewSet):

    @swagger_auto_schema(
        operation_description="Register a new hotel manager",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'name', 'last_name', 'national_code', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'national_code': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            201: openapi.Response(
                description="Created",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {
                        "data": {
                            "user": {"email": "manager@example.com", "name": "John", "last_name": "Doe"},
                            "national_code": "1234567890"
                        },
                        "message": "hotel manager created not active enter otp code"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING),
                        'errors': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                ),
                examples={
                    "application/json": {"error": "hotel manager exists"}
                }
            )
        }
    )
    def create(self, request):
        # Validate required fields
        required_fields = ['email', 'name', 'last_name', 'national_code', 'password']
        missing_fields = [field for field in required_fields if not request.data.get(field)]
        
        if missing_fields:
            return Response({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        email = request.data.get('email', '').strip()
        
        # Check if email is valid
        if not email or '@' not in email:
            return Response({"error": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if hotel manager already exists
        try:
            if HotelManager.objects.filter(user__email=email).exists():
                return Response({"error": "hotel manager exists"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error checking existing hotel manager: {str(e)}")
            
        # Check if user already exists
        try:
            if User.objects.filter(email=email).exists():
                return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error checking existing user: {str(e)}")

        data = request.data
        
        # Validate data with serializer first
        serializer = HotelManagerSerializer(data=data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Create user
                try:
                    user = User.objects.create_user(
                        email=data['email'].strip(),
                        name=data['name'].strip(),
                        last_name=data['last_name'].strip(),
                        role="Hotel Manager",
                        password=data['password'],
                        is_active=False
                    )
                    logger.info(f"User created successfully: {user.email}")
                except Exception as e:
                    logger.error(f"Error creating user: {str(e)}")
                    raise Exception(f"Failed to create user: {str(e)}")
                
                # Create hotel manager
                try:
                    manager = HotelManager.objects.create(
                        user=user,
                        national_code=data['national_code'].strip(),
                    )
                    logger.info(f"Hotel manager created successfully: {manager.id}")
                except Exception as e:
                    logger.error(f"Error creating hotel manager: {str(e)}")
                    raise Exception(f"Failed to create hotel manager: {str(e)}")
                
                # Create email verification
                try:
                    verification = EmailVerificationCode.objects.create(user=user)
                    logger.info(f"Email verification code created: {verification.id}")
                except Exception as e:
                    logger.error(f"Error creating email verification: {str(e)}")
                    raise Exception(f"Failed to create email verification: {str(e)}")
                
                # Send verification email
                try:
                    send_verification_email(user, verification)
                    logger.info(f"Verification email sent to: {user.email}")
                except Exception as e:
                    logger.error(f"Error sending verification email: {str(e)}")
                    # Don't fail the transaction for email sending issues
                    # Just log the error and continue
                
                return Response({
                    'data': HotelManagerSerializer(manager).data,
                    'message': "hotel manager created not active enter otp code"
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            return Response({
                "error": f"Failed to create hotel manager: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Login as hotel manager",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {
                        "data": {
                            "user": {"email": "manager@example.com", "name": "John", "last_name": "Doe"},
                            "national_code": "1234567890"
                        },
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"error": "Invalid credentials"}
                }
            ),
            404: openapi.Response(
                description="Not Found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"error": "hotel manager not found"}
                }
            )
        }
    )
    def retrieve(self, request):
        email = request.data.get('email', '')
        password = request.data.get('password', '')
        
        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            # Check password
            if not user.check_password(password):
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not user.is_active:
                return Response({"error": "Account is not active"}, status=status.HTTP_400_BAD_REQUEST)
            
            hotel_manager = HotelManager.objects.get(user__email=email)
            serializer = HotelManagerSerializer(hotel_manager)
            refresh = RefreshToken.for_user(user)
            return Response({
                "data": serializer.data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "user does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return Response({"error": "Login failed"}, status=status.HTTP_400_BAD_REQUEST)