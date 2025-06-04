from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import Customer, Admin, EmailVerificationCode
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()

class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        
        self.customer_data = {
            'email': 'ssaharr2020@gmail.com',
            'name': 'John',
            'last_name': 'Doe',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'Customer'
        }

        self.user = User.objects.create_user(
            email='test@example.com',
            password='asefwegg!',
            name='Test',
            last_name='User',
            role='Customer',
            is_active=True,
        )
        

    
    def test_register_verify_token_login_customer(self):


        response = self.client.post(
            '/auth/register/',
            data=json.dumps(self.customer_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(f"register-> {response.data}")


        data = {
            'email' :'ssaharr2020@gmail.com',
            'verification_code' : EmailVerificationCode.objects.get(user__email='ssaharr2020@gmail.com').code,
        }
        response = self.client.post('/auth/verify-email/', data=data)
        print(f"verify-> {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(email=data['email'])
        print(user)
        data = {
            'email': 'ssaharr2020@gmail.com',
            'password': 'StrongPass123!',
        }
        response = self.client.post('/auth/token/login/', data=data)
        print(f"verify-> {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        

    

    
    def test_register_invalid_data(self):
        # Test with mismatched passwords
        invalid_data = self.customer_data.copy()
        invalid_data['password2'] = 'DifferentPass123!'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        
        # Test with missing hotel manager data
        invalid_manager = {
            'email': 'manager@example.com',
            'name': 'Jane',
            'last_name': 'Smith',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'HotelManager'
            # Missing manager_profile field
        }
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_manager),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('manager_profile', response.data)

class LoginViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')
        
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            name='Test',
            last_name='User',
            role='Customer'
        )
        Customer.objects.create(
            user=self.user,
        )
    
    def test_login_valid_credentials(self):



        response = self.client.post(
            self.login_url,
            data={
                'email': 'test@example.com',
                'password': 'TestPass123!'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        
        user_data = response.data['user']
        self.assertEqual(user_data['email'], 'test@example.com')
    
    def test_login_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            data={
                'email': 'test@example.com',
                'password': 'WrongPassword'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

class UserProfileViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.profile_url = reverse('user_profile')
        
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            name='Test',
            last_name='User',
            role='Customer'
        )
        Customer.objects.create(
            user=self.user,
            customerID='CUST-12345678'
        )
    
    def test_get_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['name'], 'Test')
        self.assertEqual(response.data['role'], 'Customer')
        self.assertEqual(response.data['customer_profile']['customerID'], 'CUST-12345678')
    
    def test_get_profile_unauthenticated(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            self.profile_url,
            data={
                'name': 'Updated',
                'last_name': 'Name'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        
        # Check database was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

class LogoutTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test',
            last_name='User'
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        self.logout_url = reverse('logout')

    def test_logout_success(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        response = self.client.post(
            self.logout_url,
            {'refresh': str(self.refresh)},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_logout_invalid_token(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        response = self.client.post(
            self.logout_url,
            {'refresh': 'invalid_token'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_unauthenticated(self):
        response = self.client.post(
            self.logout_url,
            {'refresh': str(self.refresh)},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)