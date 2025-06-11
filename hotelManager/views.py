from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction

from accounts.models import User, EmailVerificationCode
from accounts.utils import send_verification_email
from hotelManager.models import HotelManager
from hotelManager.serializers import HotelManagerSerializer


class HotelManagerViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all hotel managers.",
        responses={200: HotelManagerSerializer(many=True), 404: 'Hotel manager not found'}
    )
    def list(self, request):
        try:
            hotel_managers = HotelManager.objects.get_all()
            serializer = HotelManagerSerializer(hotel_managers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Partially update the authenticated hotel manager’s information.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
                'national_code': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={200: HotelManagerSerializer, 400: 'Validation error', 404: 'Hotel manager not found'}
    )
    def partial_update(self, request):
        user_email = request.user.email
        try:
            hotel_manager = HotelManager.objects.get(user__email=user_email)
            data = request.data
            serializer = HotelManagerSerializer(hotel_manager, data=data, partial=True)
            # Validate only the fields that can be updated
            # To handle password update, do separately:
            if 'password' in data:
                hotel_manager.user.set_password(data['password'])
                hotel_manager.user.save()
            if serializer.is_valid():
                serializer.save()
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Delete the authenticated hotel manager.",
        responses={204: 'Deleted successfully'}
    )
    def destroy(self, request):
        # Implement delete logic if needed
        return Response({"message": "not implemented"}, status=status.HTTP_204_NO_CONTENT)


class NoneAuthHotelManagerViewSet(viewsets.ViewSet):

    @swagger_auto_schema(
        operation_description="Register a new hotel manager (unauthenticated). Sends OTP email.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'last_name', 'email', 'password', 'national_code'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
                'national_code': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={201: 'Hotel manager created and OTP sent', 400: 'Hotel manager already exists or validation error'}
    )
    def create(self, request):
        try:
            if HotelManager.objects.filter(user__email=request.data['email']).exists():
                return Response({"error": "hotel manager exists"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            return Response({"error": "email is required"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = HotelManagerSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
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
                    'message': "hotel manager created, not active, enter OTP code"
                }, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Login hotel manager and return access token.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
            },
        ),
        responses={200: openapi.Response("Successful login", HotelManagerSerializer), 404: 'User or hotel manager not found'}
    )
    def retrieve(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({"error": "email and password required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            hotel_manager = HotelManager.objects.get(user__email=email)
            if not user.check_password(password):
                return Response({"error": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

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
