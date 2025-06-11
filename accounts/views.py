from django.db import transaction
from django.contrib.auth import authenticate
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
            
            # Check if user already exists
            if User.objects.filter(email=validated_data['email']).exists():
                return Response({
                    'error': 'User with this email already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=validated_data['email'],
                        name=validated_data['name'],
                        last_name=validated_data['last_name'],
                        national_code=validated_data.get('national_code', ''),  # Handle optional field
                        role='Customer',
                        password=validated_data['password'],
                        is_active=False  # User won't be active until email is verified
                    )
                    verification = EmailVerificationCode.objects.create(user=user)
                    send_verification_email(user, verification)
                    
                return Response({
                    'user': UserSerializer(user).data,
                    'message': 'User created successfully. Please check your email for verification.'
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'error': f'Failed to create user: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        return Response({
            'error': 'Invalid data provided',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

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
            401: 'Invalid credentials',
            403: 'Account not verified'
        },
        operation_description="Authenticate a user and return JWT tokens.",
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get user first to check if they exist
            user = User.objects.get(email=email)
            
            # Check if user account is verified
            if not user.is_active:
                return Response({
                    'error': 'Account not verified. Please check your email for verification code.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Use Django's authenticate method to validate password
            authenticated_user = authenticate(username=email, password=password)
            
            if authenticated_user:
                refresh = RefreshToken.for_user(authenticated_user)
                return Response({
                    'user': UserSerializer(authenticated_user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'message': 'Login successful'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except User.DoesNotExist:
            return Response({
                'error': 'User does not exist'
            }, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'verification_code': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['email', 'verification_code']
        ),
        responses={
            200: openapi.Response(
                description="Email verified successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'access': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: 'Bad Request',
            404: 'Verification code not found'
        },
        operation_description="Verify user's email using the verification code.",
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='verify-email')
    def verify_email(self, request):
        email = request.data.get('email')
        verification_code = request.data.get('verification_code')
        
        if not email or not verification_code:
            return Response({
                'error': 'Email and verification code are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            verification = EmailVerificationCode.objects.get(
                user__email=email,
                is_verified=False  # Only get unverified codes
            )
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
                    "message": "Email verified successfully",
                    "user": UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid verification code'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except EmailVerificationCode.DoesNotExist:
            return Response({
                'error': 'Verification code not found or already used'
            }, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL)
            },
            required=['email']
        ),
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
            400: 'Bad Request',
            404: 'User not found'
        },
        operation_description="Resend email verification code to the user's email.",
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='resend-verification-code')
    def resend_verification_code(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            
            # Check if user is already verified
            if user.is_active:
                return Response({
                    'error': 'Account is already verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Delete existing verification codes
                EmailVerificationCode.objects.filter(user=user).delete()
                # Create new verification code
                verification = EmailVerificationCode.objects.create(user=user)
                send_verification_email(user, verification)

            return Response({
                "status": "success",
                "message": "A new verification code has been sent to your email."
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)


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
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({
                    "error": "Refresh token is required"
                }, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                "message": "Logout successful"
            }, status=status.HTTP_205_RESET_CONTENT)
            
        except Exception as e:
            return Response({
                "error": f"Invalid token: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)