# views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from hotel.models import Hotel
from room.models import Room
from room.serializer import RoomSerializer
from reservation.models import Reservation
from django.db.models import Q
from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RoomViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get available rooms in a city for given dates and room preferences",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['city', 'check_in_date', 'check_out_date', 'rooms'],
            properties={
                'city': openapi.Schema(type=openapi.TYPE_STRING),
                'check_in_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'check_out_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'rooms': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['type_of_room', 'number_of_passengers', 'number_of_rooms'],
                        properties={
                            'type_of_room': openapi.Schema(type=openapi.TYPE_STRING),
                            'number_of_passengers': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'number_of_rooms': openapi.Schema(type=openapi.TYPE_INTEGER),
                        }
                    )
                ),
            }
        ),
        responses={200: 'Available rooms list', 400: 'Validation error'}
    )

    def list(self, request):

        try:
            data = request.data
            city = data.get('city')
            check_in_date = data.get('check_in_date')
            check_out_date = data.get('check_out_date')
            rooms = data.get('rooms', [])
            if not rooms:
                return Response(
                    {"error": "At least one room must be specified"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not city:
                return Response(
                    {"error": "city is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not check_in_date or not check_out_date:
                return Response(
                    {"error": "Both check_in_date and check_out_date are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
                check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()

                if check_in >= check_out:
                    return Response(
                        {"error": "check_out_date must be after check_in_date"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            all_rooms = Room.objects.filter(hotel__location__istartswith=city)
            conflicting_rooms = Reservation.objects.filter(
                Q(check_in_date__lt=check_out) & Q(check_out_date__gt=check_in),
                status='confirmed'
            ).values_list('room_id', flat=True)
            available_rooms = all_rooms.exclude(id__in=conflicting_rooms)
            response_data = {
                'available_rooms': {},
                'unavailable_types': []
            }
            for room in rooms:
                room_type = room.get('type_of_room')
                passengers = room.get('number_of_passengers')
                room_count = room.get('number_of_rooms')

                if not all([room_type ,passengers, room_count]):
                    return Response(
                        {"error": "Each room must have room type ,passengers and count"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                type_rooms = available_rooms.filter(room_type=room_type)
                available_count = type_rooms.count()

                if available_count >= room_count:
                    rooms_to_book = type_rooms[:room_count]
                    response_data['available_rooms'][room_type] = {
                        'available': True,
                        'count': available_count,
                        'rooms': RoomSerializer(rooms_to_book, many=True).data,
                        'passengers_per_room': passengers,
                        'rooms_needed': room_count
                    }
                else:
                    response_data['available_rooms'][room_type] = {
                        'available': False,
                        'count': available_count,
                        'rooms_needed': room_count
                    }
                    response_data['unavailable_types'].append(room_type)



            return Response(
                {"data": response_data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Create a new room (Only by the hotel manager)",
        request_body=RoomSerializer,
        responses={201: RoomSerializer(), 400: 'Validation error'}
    )

    def create(self, request):
        """Create a new room for a hotel"""
        try:
            # Verify the requesting user is the hotel manager
            user_email = request.user
            hotel_id = request.data.get('hotel')

            if not Hotel.objects.filter(
                    id=hotel_id,
                    hotel_manager__user__email=user_email
            ).exists():
                return Response(
                    {"error": "You don't have permission to add rooms to this hotel"},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = RoomSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Retrieve a specific room by ID",
        responses={200: RoomSerializer(), 404: 'Room not found'}
    )

    
    def retrieve(self, request, pk=None):
        """Get details of a specific room"""
        try:
            # Get all rooms for the given hotel ID
            rooms = Room.objects.filter(hotel_id=pk)
            
            # Check if any rooms exist for this hotel
            if not rooms.exists():
                return Response(
                    {"error": "No rooms found for this hotel"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Serialize the queryset (many=True since it's multiple objects)
            serializer = RoomSerializer(rooms, many=True)
            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

    @swagger_auto_schema(
        operation_description="Partially update a room (Only by the hotel manager)",
        request_body=RoomSerializer,
        responses={200: RoomSerializer(), 400: 'Validation error', 403: 'Permission denied'}
    )
    def partial_update(self, request):
        """Update a room's details"""
        try:
            room = Room.objects.get(pk=request.data.get("room_id"))

            # Verify the requesting user is the hotel manager
            if not Hotel.objects.filter(
                    id=room.hotel.id,
                    hotel_manager__user__email=request.user
            ).exists():
                return Response(
                    {"error": "You don't have permission to update this room"},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = RoomSerializer(room, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"data": serializer.data},
                    status=status.HTTP_200_OK
                )
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Delete a room (Only by the hotel manager)",
        responses={204: 'Room deleted successfully', 403: 'Permission denied', 404: 'Room not found'}
    )
    def destroy(self, request, pk=None):
        """Delete a room"""
        try:
            room = Room.objects.get(pk=pk)

            # Verify the requesting user is the hotel manager
            if not Hotel.objects.filter(
                    id=room.hotel.id,
                    hotel_manager__user__email=request.user
            ).exists():
                return Response(
                    {"error": "You don't have permission to delete this room"},
                    status=status.HTTP_403_FORBIDDEN
                )

            room.delete()
            return Response(
                {"message": "Room deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class RoomDiscountViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Apply a discount to a room",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['discount_percentage'],
            properties={
                'discount_percentage': openapi.Schema(type=openapi.TYPE_NUMBER)
            }
        ),
        responses={200: RoomSerializer(), 400: 'Validation error', 403: 'Permission denied'}
    )
    def apply_discount(self, request, pk=None):
        """Apply discount to a room"""
        try:
            room = Room.objects.get(pk=pk)

            # Verify the requesting user is the hotel manager
            if not Hotel.objects.filter(
                    id=room.hotel.id,
                    hotel_manager__user__email=request.user
            ).exists():
                return Response(
                    {"error": "You don't have permission to modify this room"},
                    status=status.HTTP_403_FORBIDDEN
                )

            discount_percentage = request.data.get('discount_percentage')
            if discount_percentage is None:
                return Response(
                    {"error": "discount_percentage is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                discount_percentage = float(discount_percentage)
                if not 0 <= discount_percentage <= 100:
                    raise ValueError
            except ValueError:
                return Response(
                    {"error": "discount_percentage must be a number between 0 and 100"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            room.apply_discount(discount_percentage)
            serializer = RoomSerializer(room)
            return Response(
                {"data": serializer.data},
                status=status.HTTP_200_OK
            )
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Remove discount from a room",
        responses={200: RoomSerializer(), 403: 'Permission denied', 404: 'Room not found'}
    )
    def remove_discount(self, request, pk=None):
        """Remove discount from a room"""
        try:
            room = Room.objects.get(pk=pk)

            # Verify the requesting user is the hotel manager
            if not Hotel.objects.filter(
                    id=room.hotel.id,
                    hotel_manager__user__email=request.user
            ).exists():
                return Response(
                    {"error": "You don't have permission to modify this room"},
                    status=status.HTTP_403_FORBIDDEN
                )

            room.remove_discount()
            serializer = RoomSerializer(room)
            return Response(
                {"data": serializer.data},
                status=status.HTTP_200_OK
            )
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found"},
                status=status.HTTP_404_NOT_FOUND
            )
