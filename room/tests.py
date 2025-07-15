from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from hotel.models import Hotel
from hotelManager.models import HotelManager
from room.models import Room, RoomType
from reservation.models import Reservation
from accounts.models import Customer, User
from datetime import timedelta
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io


class RoomModelTest(TestCase):
    """Test cases for Room model"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        # Create user and hotel manager
        self.user = User.objects.create_user(
            email='manager@test.com',
            password='testpass123'
        )
        self.hotel_manager = HotelManager.objects.create(
            user=self.user,
            national_code='1234567890'
        )

        # Create hotel
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            location='Test City/street/112',
            hotel_manager=self.hotel_manager,
            status='Accepted'
        )

        # Create test rooms
        self.room1 = Room.objects.create(
            hotel=self.hotel,
            room_number = 1,
            name='1',
            room_type=RoomType.SINGLE,
            price=Decimal('100.00'),
        )
        self.room2 = Room.objects.create(
            hotel=self.hotel,
            room_number = 2,
            name='2',
            room_type=RoomType.SINGLE,
            price=Decimal('100.00'),
        )
        self.room3 = Room.objects.create(
            hotel=self.hotel,
            room_number = 3,
            name='3',
            room_type=RoomType.DOUBLE,
            price=Decimal('150.00'),
        )
        self.room4 = Room.objects.create(
            hotel=self.hotel,
            room_number = 4,
            name='4',
            room_type=RoomType.TRIPLE,
            price=Decimal('200.00'),
        )
        #
        self.regular_user = User.objects.create_user(email='user@example.com', password='testpass')

        # Create test customer
        self.customer = Customer.objects.create(
            user=self.regular_user,
        )

        # Create test reservation
        self.check_in = timezone.now().date() + timedelta(days=5)
        self.check_out = self.check_in + timedelta(days=3)
        self.reservation = Reservation.objects.create(
            room=self.room4,
            customer=self.customer,
            check_in_date=self.check_in,
            check_out_date=self.check_out,
            status='confirmed'
        )

        self.client.force_authenticate(user=self.user)

    def generate_image(self):
        image = Image.new('RGB', (100, 100), color='blue')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        return SimpleUploadedFile('hotel.jpg', image_io.read(), content_type='image/jpeg')

    def test_create_room_success(self):
        """Test successfully creating a new room"""
        data = {
            "image": self.generate_image(),
            'hotel': self.hotel.id,
            'room_number' : 109,
            'name':'test room',
            'room_type': 'Single',
            'price': 300,
        }

        response = self.client.post('/room-api/create/', data,  format='multipart')
        print(f"response -> {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_available_rooms_success(self):
        """Test successfully listing available rooms"""
        # Dates that don't conflict with existing reservation
        # check_in = (self.check_out + timedelta(days=1)).strftime('%Y-%m-%d')
        # check_out = (self.check_out + timedelta(days=3)).strftime('%Y-%m-%d')

        data = {
            'city': 'Test City',
            'check_in_date': self.check_in + timedelta(hours=48),
            'check_out_date': self.check_out,
            'rooms': [
                {
                    'type_of_room': RoomType.SINGLE,
                    'number_of_passengers': 2,
                    'number_of_rooms': 2
                },
                {
                    'type_of_room': RoomType.DOUBLE,
                    'number_of_passengers': 2,
                    'number_of_rooms': 1
                },
                {
                    'type_of_room': RoomType.TRIPLE,
                    'number_of_passengers': 3,
                    'number_of_rooms': 1
                }
            ]
        }
        response = self.client.post('/room-api/all-rooms/', data, format='json')
        print(f"response -> {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['available_rooms'][RoomType.SINGLE]['available'])
        self.assertTrue(response.data['data']['available_rooms'][RoomType.DOUBLE]['available'])
        self.assertEqual(len(response.data['data']['available_rooms'][RoomType.SINGLE]['rooms']),2)
        self.assertEqual(len(response.data['data']['available_rooms'][RoomType.DOUBLE]['rooms']), 1)




