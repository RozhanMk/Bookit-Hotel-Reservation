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
from rest_framework import status


class HotelManagerViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List all hotel managers",
        operation_description="Retrieve a list of all hotel managers in the system",
        responses={
            200: openapi.Response(
                description="Successfully retrieved hotel managers",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'user': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'email': openapi.Schema(type=openapi.TYPE_STRING),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            ),
                            'national_code': openapi.Schema(type=openapi.TYPE_STRING),
                            'status': openapi.Schema(type=openapi.TYPE_STRING),
                            'verificationFile': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI),
                        }
                    )
                )
            ),
            404: openapi.Response(
                description="Hotel managers not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        tags=['Hotel Manager - Authenticated']
    )
    def list(self, request):
        try:
            hotel_managers = HotelManager.objects.get_all()
            serializer = HotelManagerSerializer(hotel_managers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_summary="Update hotel manager profile",
        operation_description="Partially update the authenticated hotel manager's profile information",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'national_code': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="National identification code (10 digits)",
                    max_length=10
                ),
                'verificationFile': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_BINARY,
                    description="Verification document file"
                ),
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['Accepted', 'Rejected', 'Pending'],
                    description="Manager verification status"
                ),
                'user': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Successfully updated hotel manager",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'user': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                                        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                                'national_code': openapi.Schema(type=openapi.TYPE_STRING),
                                'status': openapi.Schema(type=openapi.TYPE_STRING),
                                'verificationFile': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI),
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request - validation errors",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'errors': openapi.Schema(type=openapi.TYPE_OBJECT)}
                )
            ),
            404: openapi.Response(
                description="Hotel manager not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        tags=['Hotel Manager - Authenticated']
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
        operation_summary="Delete hotel manager",
        operation_description="Delete the authenticated hotel manager account",
        responses={
            204: openapi.Response(description="Successfully deleted hotel manager"),
            404: openapi.Response(
                description="Hotel manager not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        tags=['Hotel Manager - Authenticated']
    )
    def destroy(self, request):
        pass


class NoneAuthHotelManagerViewSet(viewsets.ViewSet):

    @swagger_auto_schema(
        operation_summary="Register new hotel manager",
        operation_description="Create a new hotel manager account. Account will be inactive until email verification is completed.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'name', 'last_name', 'password', 'national_code'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="Hotel manager's email address"
                ),
                'name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Hotel manager's first name"
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Hotel manager's last name"
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description="Account password"
                ),
                'national_code': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="National identification code (10 digits)",
                    max_length=10
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Hotel manager created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'user': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                                        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                        'role': openapi.Schema(type=openapi.TYPE_STRING),
                                        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    }
                                ),
                                'national_code': openapi.Schema(type=openapi.TYPE_STRING),
                                'status': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request - validation errors or manager already exists",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING),
                        'errors': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        },
        tags=['Hotel Manager - Public']
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
        operation_summary="Hotel manager login",
        operation_description="Authenticate hotel manager and return access token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="Hotel manager's email address"
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description="Account password"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Successfully authenticated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'user': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                                        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                        'role': openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                                'national_code': openapi.Schema(type=openapi.TYPE_STRING),
                                'status': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'access': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="JWT access token"
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="Hotel manager or user not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        tags=['Hotel Manager - Public']
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