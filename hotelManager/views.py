from datetime import datetime
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import ExtractMonth
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import User, EmailVerificationCode
from accounts.serializers import UserSerializer
from hotel.models import Hotel
from hotelManager.models import HotelManager
from hotel.serializers import DiscountSerializer, HotelSerializer
from hotelManager.serializers import HotelManagerSerializer, HotelReservationsSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from accounts.utils import send_verification_email
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from reservation.models import Reservation, Payment


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

    def monthly_reservations(self, request):
        """
        Get monthly reservations for all hotels managed by the authenticated hotel manager.
        Returns a dictionary with hotel names as keys and monthly reservation counts as values.
        """
        try:
            hotel_manager = HotelManager.objects.get(user=request.user)
            hotels = Hotel.objects.filter(hotel_manager=hotel_manager)

            response_data = {}

            current_year = datetime.now().year

            for hotel in hotels:
                reservations = Reservation.objects.filter(
                    room__hotel=hotel,
                    check_in_date__year=current_year
                ).annotate(
                    month=ExtractMonth('check_in_date')
                ).values('month').annotate(
                    count=Count('id')
                ).order_by('month')

                monthly_counts = {month: 0 for month in range(1, 13)}

                for entry in reservations:
                    monthly_counts[entry['month']] = entry['count']

                response_data[hotel.name] = {
                    'year': current_year,
                    'monthly_reservations': monthly_counts
                }

            return Response(response_data, status=status.HTTP_200_OK)

        except HotelManager.DoesNotExist:
            return Response(
                {"error": "Hotel manager not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def reservation_stats(self, request):
        """
        Get reservation statistics between two dates for all hotels managed by the authenticated hotel manager.
        Query parameters:
        - start_date: YYYY-MM-DD format (required)
        - end_date: YYYY-MM-DD format (required)

        Returns:
        - total_reservations: Count of reservations between dates
        - total_revenue: Sum of payment amounts for these reservations
        - hotels: List of hotels with their individual stats
        """
        try:
            start_date_str = request.data.get('start_date')
            end_date_str = request.data.get('end_date')

            if not start_date_str or not end_date_str:
                return Response({"error":"Both start_date and end_date parameters are required"})

            try:
                start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
                end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d'))
            except ValueError:
                return Response({"error":"Dates must be in YYYY-MM-DD format"})

            if start_date > end_date:
                return Response({"error":"start_date must be before end_date"})

            hotel_manager = HotelManager.objects.get(user=request.user)
            hotels = Hotel.objects.filter(hotel_manager=hotel_manager)

            response_data = {
                'start_date': start_date_str,
                'end_date': end_date_str,
                'total_reservations': 0,
                'total_revenue': 0,
                'hotels': []
            }
            for hotel in hotels:
                reservations = Reservation.objects.filter(
                    room__hotel=hotel,
                    check_in_date__gte=start_date,
                    check_out_date__lte=end_date,
                    status='confirmed'
                )
                print(f"start-end-> {start_date}, {end_date}")
                for r in reservations:
                    print(f"reserves-> {r.check_in_date},,{r.check_out_date}")
                payment_stats = Payment.objects.filter(
                    reservation__in=reservations,
                    status='confirmed'
                ).aggregate(
                    total_amount=Sum('amount'),
                    reservation_count=Count('id')
                )

                hotel_data = {
                    'hotel_id': hotel.id,
                    'hotel_name': hotel.name,
                    'reservation_count': payment_stats['reservation_count'] or 0,
                    'revenue': float(payment_stats['total_amount'] or 0)
                }

                response_data['hotels'].append(hotel_data)
                response_data['total_reservations'] += hotel_data['reservation_count']
                response_data['total_revenue'] += hotel_data['revenue']

            return Response(response_data, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except HotelManager.DoesNotExist:
            return Response(
                {"error": "Hotel manager not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def set_discount_on_hotel(self, request):
        try:
            user_email = request.user.email
            hotel_manager = HotelManager.objects.get(user__email=user_email)
            discount_serial = DiscountSerializer(data=request.data)
            if discount_serial.is_valid():
                start_date = request.data.get("discount_start_date")
                end_date = request.data.get("discount_end_date")
                discount_amount = request.data.get("discount")
                hotel_id = request.data.get("hotel_id")
                hotel = Hotel.objects.get(id=hotel_id, hotel_manager=hotel_manager)
                hotel.discount = discount_amount
                hotel.discount_start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
                hotel.discount_end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
                hotel.discount_status = "Active"
                hotel.save()
                serializer = HotelSerializer(hotel)
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"error":discount_serial.errors}, status=status.HTTP_400_BAD_REQUEST)
        except HotelManager.DoesNotExist:
            return Response({"error": "hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)
        except Hotel.DoesNotExist:
            return Response({"error": "hotel does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error":str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def list_reservations_of_hotels(self, request):
        try:
            user_email = request.user.email
            hotel_manager = HotelManager.objects.get(user__email=user_email)
            hotels = Hotel.objects.filter(hotel_manager=hotel_manager)
            serial = HotelReservationsSerializer(hotels, many=True)
            return Response({"data":serial.data}, status=status.HTTP_200_OK)
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
        try:
            # Check if hotel manager already exists
            email = request.data.get('email', '')
            if HotelManager.objects.filter(user__email=email).exists():
                return Response({"error": "hotel manager exists"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            pass

        data = request.data
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
            except Exception as e:
                return Response({"error": "Failed to create hotel manager"}, status=status.HTTP_400_BAD_REQUEST)
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
            return Response({"error": "Login failed"}, status=status.HTTP_400_BAD_REQUEST)



