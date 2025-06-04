from rest_framework.test import APITestCase, APIClient
import os
from bookit.settings import MEDIA_ROOT
from rest_framework import status
from hotelManager.models import HotelManager
from accounts.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

class HotelManagerViewSetTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

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