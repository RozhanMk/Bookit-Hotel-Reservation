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
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class HotelManagerViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all hotel managers",
        responses={
            200: HotelManagerSerializer(many=True),
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
            hotel_managers = HotelManager.objects.get_all()
            serializer = HotelManagerSerializer(hotel_managers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Update authenticated hotel manager's profile",
        request_body=HotelManagerSerializer,
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'data': HotelManagerSerializer()
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
    def partial_update(self, request):
        user_email = request.user
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
            )
        }
    )
    def destroy(self, request):
        pass


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
                        'data': HotelManagerSerializer(),
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
                    "application/json": {"error": "hotel manager exists"},
                    "application/json": {"errors": {"email": ["This field is required."]}}
                }
            )
        }
    )
    def create(self, request):
        try:
            hotel_manager = HotelManager.objects.get(user__email=request.data['email'])
            if hotel_manager:
                return Response({"error": "hotel manager exists"}, status=status.HTTP_400_BAD_REQUEST)
        except HotelManager.DoesNotExist:
            user = None
            data = request.data
            serializer = HotelManagerSerializer(data=data)
            if serializer.is_valid():
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=data['email'],
                        name=data['name'],
                        last_name=data['last_name'],
                        role="Hotel Manager",
                        password=data['password'],
                        is_active=False
                    )
                    manager = HotelManager.objects.create(
                        user=user,
                        national_code=data['national_code'],
                    )
                verification = EmailVerificationCode.objects.create(user=user)
                send_verification_email(user, verification)
                return Response({
                    'data': HotelManagerSerializer(manager).data,
                    'message': "hotel manager created not active enter otp code"
                }, status=status.HTTP_201_CREATED)
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

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
                        'data': HotelManagerSerializer(),
                        'access': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {
                        "data": {
                            "user": {"email": "manager@example.com", "name": "John", "last_name": "Doe"},
                            "national_code": "1234567890"
                        },
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    }
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
                    "application/json": {"error": "hotel manager not found"},
                    "application/json": {"error": "user does not exist"}
                }
            )
        }
    )
    def retrieve(self, request):
        email = request.data['email']
        password = request.data['password']
        try:
            user = User.objects.get(email=email)
            hotel_manager = HotelManager.objects.get(user__email=email)
            serializer = HotelManagerSerializer(hotel_manager)
            refresh = RefreshToken.for_user(user)
            return Response({
                "data": serializer.data,
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "user does not exist"}, status=status.HTTP_404_NOT_FOUND)