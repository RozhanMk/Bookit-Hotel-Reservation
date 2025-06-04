from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from hotel.models import Hotel, HotelFacility, Facility
from hotelManager.models import HotelManager
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

User = get_user_model()

class HotelViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='pass1234')
        self.hotel_manager = HotelManager.objects.create(
            user=self.user,
            national_code='1234567890',
            verificationFile=SimpleUploadedFile(
                name='verify.pdf',
                content=b'%PDF dummy',
                content_type='application/pdf'
            )
        )
        self.wifi_facility = HotelFacility.objects.create(facility_type=Facility.WIFI)
        self.parking_facility = HotelFacility.objects.create(facility_type=Facility.PARKING)
        self.client.force_authenticate(user=self.user)

    def generate_image(self):
        image = Image.new('RGB', (100, 100), color='blue')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        return SimpleUploadedFile('hotel.jpg', image_io.read(), content_type='image/jpeg')

    def generate_pdf(self):
        return SimpleUploadedFile(
            name='license.pdf',
            content=b'%PDF license',
            content_type='application/pdf'
        )

    def test_create_hotel_success(self):
        url = '/hotel-api/hotel/'
        data = {
            "name": "Sunset Hotel",
            "location": "Coastal City",
            "description": "A nice view hotel",
            "image": self.generate_image(),
            "hotel_license": self.generate_image(),
            "hotel_iban_number": "123456789012345678901234",
            "facilities": ["Wi-Fi", "Parking"],
        }

        response = self.client.post(url, data, format='multipart')
        print(f"response -> {response}")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Hotel.objects.count(), 1)
        self.assertEqual(Hotel.objects.first().name, "Sunset Hotel")


    def test_create_facs(self):
        data={"name" : "re"}
        resp = self.client.post('/hotel-api/add-fac/', data, format='multipart')
        print(resp)

    def test_create_hotel_duplicate_location(self):
        # First hotel
        Hotel.objects.create(
            hotel_manager=self.hotel_manager,
            name="Hotel A",
            location="City X",
            description="Desc",
            image=self.generate_image(),
            hotel_license=self.generate_pdf(),
            hotel_iban_number="000000000000000000000000"
        )

        url = '/hotel-api/hotel/'
        data = {
            "name": "Hotel B",
            "location": "City X",  # duplicate location
            "description": "Another",
            "image": self.generate_image(),
            "hotel_license": self.generate_pdf(),
            "hotel_iban_number": "123456789012345678901234",
            "facilities": [self.wifi_facility.facility_type, self.parking_facility.facility_type]
        }

        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Hotel already exists', response.data['error'])

    def test_retrieve_user_hotels(self):
        # Create hotel for current user
        hotel = Hotel.objects.create(
            hotel_manager=self.hotel_manager,
            name="Hotel Z",
            location="Mountain City",
            description="Test",
            image=self.generate_image(),
            hotel_license=self.generate_image(),
            hotel_iban_number="111111111111111111111111"
        )

        url = f'/hotel-api/hotel/{hotel.pk}/'  # GET one hotel by pk
        response = self.client.get(url)
        print(f"response -> {response.data}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['name'], "Hotel Z")

    def test_list_user_hotels(self):
        # Create one or more hotels for current user
        Hotel.objects.create(
            hotel_manager=self.hotel_manager,
            name="User Hotel 1",
            location="Loc 1",
            description="Desc 1",
            image=self.generate_image(),
            hotel_license=self.generate_image(),
            hotel_iban_number="123456789012345678901234"
        )

        url = '/hotel-api/hotel/'  # GET list user's hotels (my_hotels)
        response = self.client.get(url)
        print(f"response -> {response.data}")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data['data']) >= 1)

    def test_list_all_hotels(self):
        other_user = User.objects.create_user(email='other@example.com', password='pass1234')
        other_manager = HotelManager.objects.create(
            user=other_user,
            national_code='1111111111',
        )
        Hotel.objects.create(
            hotel_manager=other_manager,
            name="Ocean View",
            location="Seaside",
            description="Nice hotel",
            image=self.generate_image(),
            hotel_license=self.generate_image(),
            hotel_iban_number="999999999999999999999999",
            status="Accepted"
        )

        url = '/hotel-api/all-hotels/'
        response = self.client.get(url)
        print(f"response -> {response.data}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], "Ocean View")