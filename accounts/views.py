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