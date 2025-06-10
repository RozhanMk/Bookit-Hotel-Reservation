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

class HotelManagerViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""
        Retrieve a list of all hotel managers.

        Requires authentication.

        Returns:
        - 200: Success, returns list of hotel managers
        - 404: If no hotel managers are found
        """,
        responses={
            200: HotelManagerSerializer(many=True),
            404: {
                'description': 'Hotel managers not found',
                'content': {
                    'application/json': {
                        'example': {'error': 'hotel manager not found'}
                    }
                }
            }
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
        operation_description="""
        Partially update the authenticated hotel manager's information.

        Requires authentication.
        Only updates fields provided in the request.

        Returns:
        - 200: Success, returns updated hotel manager data
        - 400: If validation errors occur
        - 404: If hotel manager is not found
        """,
        request_body=HotelManagerSerializer,
        responses={
            200: {
                'description': 'Updated hotel manager data',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'data': HotelManagerSerializer()
                            }
                        }
                    }
                }
            },
            400: {
                'description': 'Validation errors',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'errors': {'type': 'object'}
                            }
                        }
                    }
                }
            },
            404: {
                'description': 'Hotel manager not found',
                'content': {
                    'application/json': {
                        'example': {'error': 'hotel manager not found'}
                    }
                }
            }
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
        operation_description="""
        Delete a hotel manager account.

        Requires authentication.
        This will permanently delete the hotel manager's account.

        Returns:
        - 204: Success, no content
        """,
        responses={
            204: {
                'description': 'Hotel manager deleted successfully',
                'content': None
            }
        }
    )
    def destroy(self, request):
        pass


class NoneAuthHotelManagerViewSet(viewsets.ViewSet):

    @swagger_auto_schema(
        operation_description="""
        Register a new hotel manager.

        Does not require authentication.
        Creates a new user with Hotel Manager role (initially inactive).
        Sends verification email with OTP code.

        Required fields:
        - email
        - name
        - last_name
        - national_code
        - password

        Returns:
        - 201: Success, returns created hotel manager data
        - 400: If validation errors occur or hotel manager already exists
        """,
        request_body={
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'email': {'type': 'string', 'format': 'email'},
                            'name': {'type': 'string'},
                            'last_name': {'type': 'string'},
                            'national_code': {'type': 'string'},
                            'password': {'type': 'string'}
                        },
                        'required': ['email', 'name', 'last_name', 'national_code', 'password']
                    }
                }
            }
        },
        responses={
            201: {
                'description': 'Hotel manager created (inactive)',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'data': HotelManagerSerializer(),
                                'message': {'type': 'string'}
                            }
                        },
                        'example': {
                            'data': HotelManagerSerializer(),
                            'message': 'hotel manager created not active enter otp code'
                        }
                    }
                }
            },
            400: {
                'description': 'Validation errors or hotel manager exists',
                'content': {
                    'application/json': {
                        'examples': {
                            'validation_error': {'value': {'errors': {}}},
                            'manager_exists': {'value': {'error': 'hotel manager exists'}}
                        }
                    }
                }
            }
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
        operation_description="""
        Retrieve a specific hotel manager by email and password (login).

        Does not require authentication.

        Parameters:
        - email: The email of the hotel manager
        - password: The password of the hotel manager

        Returns:
        - 200: Success, returns hotel manager data with access token
        - 404: If hotel manager or user is not found
        """,
        request_body={
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'email': {'type': 'string', 'format': 'email'},
                            'password': {'type': 'string'}
                        },
                        'required': ['email', 'password']
                    }
                }
            }
        },
        responses={
            200: {
                'description': 'Hotel manager data with access token',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'data': HotelManagerSerializer(),
                                'access': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            404: {
                'description': 'Hotel manager or user not found',
                'content': {
                    'application/json': {
                        'examples': {
                            'manager_not_found': {'value': {'error': 'hotel manager not found'}},
                            'user_not_found': {'value': {'error': 'user does not exist'}}
                        }
                    }
                }
            }
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
