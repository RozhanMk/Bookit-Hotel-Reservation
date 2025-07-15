from rest_framework.test import APIClient
import os
from bookit.settings import MEDIA_ROOT
from accounts.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from hotelManager.models import HotelManager
from hotel.models import Hotel
from room.models import Room
from reservation.models import Reservation, Payment
from accounts.models import Customer

class HotelManagerViewSetTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.customer_user = User.objects.create_user(
            email='customer@test.com',
            password='testpass123',
            name='John',
            last_name='Doe'
        )
        self.customer = Customer.objects.create(user=self.customer_user)
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123'
        )

        # Authenticate the client
        self.client.force_authenticate(user=self.user)

        # Create a hotel manager linked to the user
        self.hotel_manager = HotelManager.objects.create(
            user=self.user,
            national_code='1234567890',
            verificationFile=SimpleUploadedFile(name='1234567890.pdf', content=b'file_content', content_type='application/pdf')
        )

        # Create test hotel and room
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            location='Test city, 123 Test St',
            description='Test description',
            hotel_iban_number='123456789012345678901234',
            hotel_manager=self.hotel_manager
        )

        self.hotel1 = Hotel.objects.create(
            name='Test testino Hotel',
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
        self.room1= Room.objects.create(
            hotel=self.hotel1,
            room_number=101,
            name='Deluxe Room',
            room_type='Double',
            price=150.00,
            rate=4,
            rate_number=10
        )

        # Create test reservation
        all_reserves = []
        self.reservation1 = Reservation.objects.create(
            room=self.room,
            customer=self.customer,
            check_in_date=timezone.now().date() + timedelta(days=1),
            check_out_date=timezone.now().date() + timedelta(days=3),
            status='confirmed'
        )
        all_reserves.append(self.reservation1)
        self.reservation2 = Reservation.objects.create(
            room=self.room,
            customer=self.customer,
            check_in_date=timezone.now().date() + timedelta(days=31),
            check_out_date=timezone.now().date() + timedelta(days=35),
            status='confirmed'
        )
        all_reserves.append(self.reservation2)
        self.reservation3 = Reservation.objects.create(
            room=self.room1,
            customer=self.customer,
            check_in_date=timezone.now().date() + timedelta(days=1),
            check_out_date=timezone.now().date() + timedelta(days=3),
            status='confirmed'
        )
        all_reserves.append(self.reservation3)
        self.reservation4 = Reservation.objects.create(
            room=self.room1,
            customer=self.customer,
            check_in_date=timezone.now().date() + timedelta(days=31),
            check_out_date=timezone.now().date() + timedelta(days=35),
            status='confirmed'
        )
        all_reserves.append(self.reservation4)

        for r in all_reserves:
            payment = Payment.objects.create(
                reservation=r,
                amount=300,
                method='online',
                status='confirmed'
            )

        self.start_date = timezone.now().date()
        self.end_date = timezone.now().date() + timedelta(days=36)


    def test_get_state_reservations_for_hotel_manager(self):
        response = self.client.post('/hotelManager-api/hotel_manager/reservation_stats/', {
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d')
        })
        print(response.data)

    def test_get_report(self):
        # test hotel manager gets report
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/hotelManager-api/hotel_manager/monthly_reservations/')
        print(f"res -> {response.data}")


    def test_list_hotel_managers(self):
        response = self.client.get("/hotelManager-api/list/")

        print(f"data -> {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_hotel_manager(self):
        response = self.client.get("/hotelManager-api/hotel-manager/")

        print(f"data -> {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['national_code'], self.hotel_manager.national_code)

    def test_partial_update_hotel_manager(self):
        new_data = {
            "national_code": "0987654321"
        }
        response = self.client.patch("/hotelManager-api/hotel-manager/", data=new_data, format='json')

        print(f"data -> {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.hotel_manager.refresh_from_db()
        self.assertEqual(self.hotel_manager.national_code, "0987654321")


    def test_partial_update_hotel_manager_with_file(self):
        # First, simulate uploading an initial verification file
        test_file = SimpleUploadedFile("old_code.pdf", b"Dummy content", content_type="application/pdf")
        self.hotel_manager.verificationFile.save(f"{self.hotel_manager.national_code}.pdf", test_file)
        self.hotel_manager.save()

        # Make sure file exists before updating
        old_file_path = os.path.join(MEDIA_ROOT, 'hotel-manager/verificationFiles',
                                     f"{self.hotel_manager.national_code}.pdf")
        self.assertTrue(os.path.exists(old_file_path))

        # Prepare new file and new national_code
        new_file = SimpleUploadedFile("new_code.pdf", b"New dummy content", content_type="application/pdf")
        new_data = {
            "national_code": "0987654321",
            "verificationFile": new_file,
        }

        response = self.client.patch(
            "/hotelManager-api/hotel-manager/",
            data=new_data,
            format='multipart'
        )

        print(f"data -> {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.hotel_manager.refresh_from_db()

        # Check national_code updated
        self.assertEqual(self.hotel_manager.national_code, "0987654321")

        # Check file renamed and saved
        new_file_path = os.path.join(MEDIA_ROOT, 'hotel-manager/verificationFiles', '0987654321.pdf')
        self.assertTrue(os.path.exists(new_file_path))
        self.assertFalse(os.path.exists(old_file_path))  # Old file should not exist anymore

        # Check instance's file name updated
        self.assertEqual(self.hotel_manager.verificationFile.name, 'hotel-manager/verificationFiles/0987654321.pdf')



    def test_create_hotel_manager_when_exists(self):
        data = {
            "user": self.user.id,
            "national_code": "1112223334",
            "verificationFile": SimpleUploadedFile(name='another_file.pdf', content=b'file_content', content_type='application/pdf')
        }
        response = self.client.post("/hotelManager-api/create/", data, format='multipart')

        print(f"data -> {response.data}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_create_hotel_manager_successfully(self):
        # Log out first user
        self.client.force_authenticate(user=None)

        # Create a new user


        data = {
            "email" : 'ssaharr2020@gmail.com',
            "password " : 'newpassword123',
            "password2 ": 'newpassword123',
            "name" : "test",
            "last_name":"test",
            "national_code": "1122334455",
            "verificationFile": SimpleUploadedFile(name='new_file.pdf', content=b'new_file_content', content_type='application/pdf')
        }
        response = self.client.post("/hotelManager-api/create/", data, format='multipart')

        print(f"data -> {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {
            "email": 'ssaharr2020@gmail.com',
            "password ": 'newpassword123',}
        response = self.client.post("/hotelManager-api/get/", data, format='multipart')
        print(f"data -> {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
