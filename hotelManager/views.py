from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import User, EmailVerificationCode
from hotelManager.models import HotelManager
from hotelManager.serializers import HotelManagerSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from accounts.utils import send_verification_email
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class HotelManagerViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_description="Get authenticated hotel manager's profile")
    def get_profile(self, request):
        try:
            hotel_manager = HotelManager.objects.get(user=request.user)
            data = {
                'email': hotel_manager.user.email,
                'name': hotel_manager.user.name,
                'last_name': hotel_manager.user.last_name,
                'national_code': hotel_manager.national_code
            }
            return Response({"data": data}, status=status.HTTP_200_OK)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(operation_description="List all hotel managers")
    def list(self, request):
        hotel_managers = HotelManager.objects.all()
        data = [
            {
                'email': hm.user.email,
                'name': hm.user.name,
                'last_name': hm.user.last_name,
                'national_code': hm.national_code
            }
            for hm in hotel_managers
        ]
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_description="Retrieve a hotel manager by ID")
    def retrieve(self, request, pk=None):
        try:
            hotel_manager = HotelManager.objects.get(pk=pk)
            data = {
                'email': hotel_manager.user.email,
                'name': hotel_manager.user.name,
                'last_name': hotel_manager.user.last_name,
                'national_code': hotel_manager.national_code
            }
            return Response({"data": data}, status=status.HTTP_200_OK)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(operation_description="Update hotel manager's profile")
    def partial_update(self, request, pk=None):
        try:
            hotel_manager = HotelManager.objects.get(user=request.user)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)

        user = hotel_manager.user
        data = request.data

        user.name = data.get('name', user.name)
        user.last_name = data.get('last_name', user.last_name)
        hotel_manager.national_code = data.get('national_code', hotel_manager.national_code)

        user.save()
        hotel_manager.save()

        updated_data = {
            'email': user.email,
            'name': user.name,
            'last_name': user.last_name,
            'national_code': hotel_manager.national_code
        }
        return Response({"data": updated_data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_description="Delete hotel manager account")
    def destroy(self, request, pk=None):
        try:
            hotel_manager = HotelManager.objects.get(user=request.user)
            hotel_manager.user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)


class NoneAuthHotelManagerViewSet(viewsets.ViewSet):

    @swagger_auto_schema(operation_description="Register a new hotel manager")
    def create(self, request):
        data = request.data
        email = data.get('email')

        if HotelManager.objects.filter(user__email=email).exists():
            return Response({"error": "hotel manager exists"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = HotelManagerSerializer(data=data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=data['email'],
                        name=data['name'],
                        last_name=data['last_name'],
                        role="Hotel Manager",
                        password=data['password'],
                        is_active=False
                    )
                    hotel_manager = HotelManager.objects.create(
                        user=user,
                        national_code=data['national_code']
                    )
                verification = EmailVerificationCode.objects.create(user=user)
                send_verification_email(user, verification)

                response_data = {
                    'user': {
                        'email': user.email,
                        'name': user.name,
                        'last_name': user.last_name
                    },
                    'national_code': hotel_manager.national_code
                }

                return Response({
                    'data': response_data,
                    'message': "hotel manager created not active enter otp code"
                }, status=status.HTTP_201_CREATED)
            except Exception:
                return Response({"error": "Failed to create hotel manager"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_description="Login as hotel manager")
    def retrieve(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

            if not user.is_active:
                return Response({"error": "Account is not active"}, status=status.HTTP_400_BAD_REQUEST)

            hotel_manager = HotelManager.objects.get(user=user)

            data = {
                'user': {
                    'email': user.email,
                    'name': user.name,
                    'last_name': user.last_name
                },
                'national_code': hotel_manager.national_code
            }

            refresh = RefreshToken.for_user(user)

            return Response({
                "data": data,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "user does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Login failed"}, status=status.HTTP_400_BAD_REQUEST)
