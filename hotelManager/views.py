from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from accounts.models import User, EmailVerificationCode
from accounts.utils import send_verification_email
from hotelManager.models import HotelManager
from .serializers import HotelManagerSerializer, HotelManagerCreateSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class HotelManagerViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return HotelManagerCreateSerializer
        return HotelManagerSerializer

    @swagger_auto_schema(
        operation_description="List all hotel managers (admin only)",
        responses={200: HotelManagerSerializer(many=True)}
    )
    def list(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to view this"},
                status=status.HTTP_403_FORBIDDEN
            )
        queryset = HotelManager.objects.all()
        serializer = HotelManagerSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new hotel manager (admin only)",
        request_body=HotelManagerCreateSerializer,
        responses={201: HotelManagerSerializer}
    )
    def create(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to create managers"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = HotelManagerCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Get hotel manager details",
        responses={200: HotelManagerSerializer}
    )
    def retrieve(self, request, pk=None):
        try:
            if pk:
                instance = HotelManager.objects.get(pk=pk)
            else:
                instance = HotelManager.objects.get(user=request.user)
            serializer = HotelManagerSerializer(instance)
            return Response(serializer.data)
        except HotelManager.DoesNotExist:
            return Response(
                {"error": "Hotel manager not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Update hotel manager details",
        request_body=HotelManagerSerializer,
        responses={200: HotelManagerSerializer}
    )
    def update(self, request, pk=None):
        try:
            instance = HotelManager.objects.get(pk=pk)
            if instance.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You can only update your own profile"},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = HotelManagerSerializer(instance, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except HotelManager.DoesNotExist:
            return Response(
                {"error": "Hotel manager not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Partial update hotel manager details",
        request_body=HotelManagerSerializer,
        responses={200: HotelManagerSerializer}
    )
    def partial_update(self, request, pk=None):
        try:
            instance = HotelManager.objects.get(pk=pk)
            if instance.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You can only update your own profile"},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = HotelManagerSerializer(
                instance, 
                data=request.data, 
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except HotelManager.DoesNotExist:
            return Response(
                {"error": "Hotel manager not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Delete a hotel manager",
        responses={204: "No content"}
    )
    def destroy(self, request, pk=None):
        try:
            instance = HotelManager.objects.get(pk=pk)
            if instance.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You can only delete your own profile"},
                    status=status.HTTP_403_FORBIDDEN
                )
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except HotelManager.DoesNotExist:
            return Response(
                {"error": "Hotel manager not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Get current hotel manager profile",
        responses={200: HotelManagerSerializer}
    )
    @action(detail=False, methods=['get'])
    def get_profile(self, request):
        try:
            instance = HotelManager.objects.get(user=request.user)
            serializer = HotelManagerSerializer(instance)
            return Response(serializer.data)
        except HotelManager.DoesNotExist:
            return Response(
                {"error": "Hotel manager not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class NoneAuthHotelManagerViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_description="Register a new hotel manager",
        request_body=HotelManagerCreateSerializer,
        responses={201: HotelManagerSerializer}
    )
    def create(self, request):
        serializer = HotelManagerCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    hotel_manager = serializer.save()
                    verification = EmailVerificationCode.objects.create(
                        user=hotel_manager.user
                    )
                    send_verification_email(hotel_manager.user, verification)

                    return Response({
                        'data': {
                            "email": hotel_manager.user.email,
                            "name": hotel_manager.user.name,
                            "last_name": hotel_manager.user.last_name,
                            "national_code": hotel_manager.national_code
                        },
                        'message': "Hotel manager created. Please verify your email."
                    }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

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
                        'data': HotelManagerSerializer,
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Invalid credentials",
            404: "User not found"
        }
    )
    def retrieve(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response(
                    {"error": "Invalid credentials"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not user.is_active:
                return Response(
                    {"error": "Account is not active"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            hotel_manager = HotelManager.objects.get(user=user)
            serializer = HotelManagerSerializer(hotel_manager)
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "data": serializer.data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)
            
        except (HotelManager.DoesNotExist, User.DoesNotExist):
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_404_NOT_FOUND
            )