from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import Customer
from hotelManager.models import HotelManager
from hotel.models import Hotel
from room.models import Room, RoomLock
from reservation.models import Reservation, Payment

User = get_user_model()


class ReservationViewSetTestCase(APITestCase):
    def setUp(self):
        # Create test users
        self.customer_user = User.objects.create_user(
            email='customer@test.com',
            password='testpass123',
            name='John',
            last_name='Doe'
        )
        self.customer = Customer.objects.create(user=self.customer_user)

        self.hotel_manager_user = User.objects.create_user(
            email='manager@test.com',
            password='testpass123',
            name='Manager',
            last_name='Smith'
        )
        self.hotel_manager = HotelManager.objects.create(user=self.hotel_manager_user)

        # Create test hotel and room
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            location='Test city, 123 Test St',
            description='Test description',
            hotel_iban_number='123456789012345678901234',
            hotel_manager=self.hotel_manager
        )

        self.room = Room.objects.create(
            hotel=self.hotel,
            room_number=101,
            name='Deluxe Room',
            room_type='Double',
            price=150.00,
            rate=4,
            rate_number=10
        )

        self.room1 = Room.objects.create(
            hotel=self.hotel,
            room_number=102,
            name='Deluxe Room',
            room_type='Double',
            price=150.00,
            rate=4,
            rate_number=10
        )

        # Create test reservation
        self.reservation = Reservation.objects.create(
            room=self.room,
            customer=self.customer,
            check_in_date=timezone.now().date() + timedelta(days=1),
            check_out_date=timezone.now().date() + timedelta(days=3),
            status='confirmed'
        )

        # Create test payment
        self.payment = Payment.objects.create(
            reservation=self.reservation,
            amount=300,
            method='online',
            status='confirmed'
        )

    def test_list_reservations_as_hotel_manager(self):
        self.client.force_authenticate(user=self.hotel_manager_user)
        response = self.client.get('/reservation-api/all-hotel-reservations/')
        print(f"res = {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)

    def test_list_reservations_as_customer(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get('/reservation-api/reservation/')
        print(f"res = {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)

    def test_list_reservations_unauthenticated(self):
        response = self.client.get('/reservation-api/all-hotel-reservations/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lock_rooms_for_user(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post('/reservation-api/lock-rooms/', {'room_numbers': ['101', '102'], 'hotel_id':self.hotel.id}, format='json')
        print(f"response -> {response}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        lock = RoomLock.objects.filter(user=self.customer_user, room=self.room).first()
        self.assertIsNotNone(lock)

    def test_lock_rooms_conflict(self):
        # First lock by another user
        other_user = User.objects.create_user(email='other@test.com', password='testpass123')
        RoomLock.objects.create(
            user=other_user,
            room=self.room,
            locked_until=timezone.now() + timedelta(minutes=30)
        )

        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post('/reservation-api/lock-rooms/',{'room_numbers': [101, 102], 'hotel_id':self.hotel.id},format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('conflicts', response.data)

    def test_unlock_rooms_for_user(self):
        # First create a lock
        RoomLock.objects.create(
            user=self.customer_user,
            room=self.room,
            locked_until=timezone.now() + timedelta(minutes=30)
        )

        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post('/reservation-api/unlock-rooms/', {'room_numbers': [101, 102]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unlocked'], 1)

        # Verify lock was removed
        lock = RoomLock.objects.filter(user=self.customer_user, room=self.room).first()
        self.assertIsNone(lock)

    def test_reserve_room_success(self):
        # First lock the room
        RoomLock.objects.create(
            user=self.customer_user,
            room=self.room1,
            locked_until=timezone.now() + timedelta(minutes=30)
        )
        self.client.force_authenticate(user=self.customer_user)
        data = {
            'room_number': 102,
            'check_in_date': (timezone.now() + timedelta(days=1)).date().isoformat(),
            'check_out_date': (timezone.now() + timedelta(days=3)).date().isoformat(),
            'amount': 300,
            'method': 'online'
        }
        response = self.client.post('/reservation-api/reserve/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Reservation and payment successful')

        # Verify reservation was created
        reservation = Reservation.objects.filter(customer=self.customer).first()
        self.assertIsNotNone(reservation)

        # Verify payment was created
        payment = Payment.objects.filter(reservation=reservation).first()
        self.assertIsNotNone(payment)

        # Verify lock was removed
        lock = RoomLock.objects.filter(user=self.customer_user, room=self.room).first()
        self.assertIsNone(lock)

    def test_reserve_room_without_lock(self):
        self.client.force_authenticate(user=self.customer_user)
        data = {
            'room_number': 101,
            'check_in_date': (timezone.now() + timedelta(days=1)).date().isoformat(),
            'check_out_date': (timezone.now() + timedelta(days=3)).date().isoformat(),
            'amount': 300,
            'method': 'online'
        }
        response = self.client.post('/reservation-api/reserve/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], 'Room not locked or lock expired')

    def test_reserve_room_with_expired_lock(self):
        # Create an expired lock
        RoomLock.objects.create(
            user=self.customer_user,
            room=self.room,
            locked_until=timezone.now() - timedelta(minutes=1)
        )

        self.client.force_authenticate(user=self.customer_user)
        data = {
            'room_number': 101,
            'check_in_date': (timezone.now() + timedelta(days=1)).date().isoformat(),
            'check_out_date': (timezone.now() + timedelta(days=3)).date().isoformat(),
            'amount': 300,
            'method': 'online'
        }
        response = self.client.post('/reservation-api/reserve/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], 'Room not locked or lock expired')

    def test_reserve_room_already_reserved(self):
        # First lock the room
        RoomLock.objects.create(
            user=self.customer_user,
            room=self.room,
            locked_until=timezone.now() + timedelta(minutes=30)
        )

        # Create an existing reservation for the room
        Reservation.objects.create(
            room=self.room,
            customer=self.customer,
            check_in_date=timezone.now().date() + timedelta(days=1),
            check_out_date=timezone.now().date() + timedelta(days=3),
            status='confirmed'
        )

        self.client.force_authenticate(user=self.customer_user)
        data = {
            'room_number': 101,
            'check_in_date': (timezone.now() + timedelta(days=1)).date().isoformat(),
            'check_out_date': (timezone.now() + timedelta(days=3)).date().isoformat(),
            'amount': 300,
            'method': 'online'
        }
        response = self.client.post('/reservation-api/reserve/', data)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['error'], 'Room already reserved')

    def test_reserve_room_missing_fields(self):
        self.client.force_authenticate(user=self.customer_user)
        data = {
            'room_number': 101,
            # Missing other required fields
        }
        response = self.client.post('/reservation-api/reserve/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing required fields')

    def test_reserve_room_not_found(self):
        self.client.force_authenticate(user=self.customer_user)
        data = {
            'room_number': 999,  # Non-existent room
            'check_in_date': (timezone.now() + timedelta(days=1)).date().isoformat(),
            'check_out_date': (timezone.now() + timedelta(days=3)).date().isoformat(),
            'amount': 300,
            'method': 'online'
        }
        response = self.client.post('/reservation-api/reserve/', data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Room not found')
