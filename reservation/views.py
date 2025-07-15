import decimal
from django.db.models import Min
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import User
from hotel.models import Hotel
from hotelManager.models import HotelManager
from reservation.models import Reservation, Payment
from .serializer import ReservationSerializer, ReservationDetailSerializer, PaymentSerializer
from room.models import Room, RoomLock
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

class ReservationViewSet(viewsets.ViewSet):

    permission_classes = [IsAuthenticated]

    def list(self, request):
        email = request.user
        try:
            hotel_manager = HotelManager.objects.get(user__email=email)
            hotel_reservations = Reservation.objects.filter(room__hotel__hotel_manager=hotel_manager)
            serializer = ReservationSerializer(hotel_reservations, many=True)
            return Response({'data':serializer.data}, status=status.HTTP_200_OK)
        except HotelManager.DoesNotExist:
            return Response({'error' : 'hotel manager not found'},status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request):
        email = request.user
        try:
            data = {}
            user = User.objects.get(email=email)
            past_room_reservations = Reservation.objects.filter(user=user, check_out_date__lte=timezone.now())
            data["past"] = ReservationSerializer(past_room_reservations, many=True).data
            future_room_reservations = Reservation.objects.filter(user=user, check_out_date__gt=timezone.now())
            data["future"] = ReservationSerializer(future_room_reservations, many=True).data
            return Response({'data': data}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'user not found'}, status=status.HTTP_404_NOT_FOUND)

    MAX_LOCKS_PER_USER = 3  # Maximum concurrent room locks per user
    LOCK_COOLDOWN_MINUTES = 5  # Minutes to wait after reaching max locks
    LOCK_TIMEOUT_MINUTES = 15  # Default lock duration
    
    def lock_rooms_for_user(self, request):
        try:
            email = request.user
            user = User.objects.get(email=email)
            room_ids = request.data.get('room_ids', [])
            
            if not room_ids:
                return Response({"error": "No room IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
            cooldown_key = f"lock_cooldown_{user.id}"
            if cache.get(cooldown_key):
                return Response({
                    "error": "You've reached your maximum lock attempts. Please wait before trying again.",
                    "cooldown_until": cache.get(cooldown_key + "_time")
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            current_locks = RoomLock.objects.filter(user=user, locked_until__gt=timezone.now())
            if current_locks.count() >= self.MAX_LOCKS_PER_USER:
                cooldown_until = timezone.now() + timedelta(minutes=self.LOCK_COOLDOWN_MINUTES)
                cache.set(cooldown_key, True, timeout=self.LOCK_COOLDOWN_MINUTES * 60)
                cache.set(cooldown_key + "_time", cooldown_until, timeout=self.LOCK_COOLDOWN_MINUTES * 60)
                return Response({
                    "error": f"You can only have {self.MAX_LOCKS_PER_USER} active room locks at a time.",
                    "cooldown_until": cooldown_until
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            now = timezone.now()
            locked_until = now + timedelta(minutes=self.LOCK_TIMEOUT_MINUTES)
            conflicting_locks = RoomLock.objects.filter(
                room_id__in=room_ids,
                locked_until__gt=now
            ).select_related('room')
            
            if conflicting_locks.exists():
                return Response({
                    "error": "Some rooms are already locked by other users.",
                    "conflicts": [lock.room.room_number for lock in conflicting_locks]
                }, status=status.HTTP_400_BAD_REQUEST)
            RoomLock.objects.filter(user=user).delete()
            available_slots = self.MAX_LOCKS_PER_USER - current_locks.count()
            room_ids = room_ids[:available_slots] 
            locks_to_create = [
                RoomLock(
                    user=user,
                    room_id=room_id,
                    locked_until=locked_until
                ) for room_id in room_ids
            ]
            RoomLock.objects.bulk_create(locks_to_create)
            
            return Response({
                "success": True, 
                "locked_until": locked_until,
                "locked_rooms": room_ids,
                "remaining_locks": available_slots - len(room_ids)
            })
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def unlock_rooms_for_user(self, request):
        try:
            email = request.user
            user = User.objects.get(email=email)
            room_ids = request.data.get('room_ids', [])
            locks = RoomLock.objects.filter(user=user)
            if room_ids:
                locks = locks.filter(room__id__in=room_ids)
                deleted_count, _ = locks.delete()
                return Response({"unlocked": deleted_count}, status=status.HTTP_200_OK)
            return Response({"error":"enter room numbers"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'user not found'}, status=status.HTTP_404_NOT_FOUND)


    def reserve(self, request):
        user = request.user
        data = request.data
        room_id = data.get('room_id')
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        method = data.get('method')

        if not all([room_id, check_in, check_out, method]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()

        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            lock = RoomLock.objects.get(user=user, room=room)
        except RoomLock.DoesNotExist:
            return Response({'error': 'Room not locked or lock expired'}, status=status.HTTP_403_FORBIDDEN)

        conflicting_reservations = Reservation.objects.filter(
        room=room,
        check_out_date__gt=check_in,
        check_in_date__lt=check_out   
        ).exclude(status='cancelled') 

        if conflicting_reservations.exists():
            return Response({
                'error': 'Room already reserved for the selected dates',
                'conflicting_dates': {
                    'earliest_available': conflicting_reservations.aggregate(
                        Min('check_out_date')
                    )['check_out_date__min']
                }
            }, status=status.HTTP_409_CONFLICT)

        reservation = Reservation.objects.create(
            room=room,
            user=user,
            check_in_date=check_in,
            check_out_date=check_out,
            status='confirmed'
        )
        amount = decimal.Decimal(room.price)
        if method == "In person":
            amount = amount/2
        print(amount)
        if room.hotel.discount_status == "Active" and room.hotel.discount_end_date is not None:
            if room.hotel.discount_end_date > timezone.now():
                amount = amount - (amount*room.hotel.discount)/100
        print(amount)
        payment = Payment.objects.create(
            reservation=reservation,
            amount=amount,
            method=method,
            status='confirmed'
        )

        lock.delete()

        return Response({
            'message': 'Reservation and payment successful',
            'reservation': ReservationSerializer(reservation).data ,
            'payment': PaymentSerializer(payment).data
        }, status=status.HTTP_201_CREATED)



