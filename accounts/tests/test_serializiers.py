# accounts/tests/test_serializers.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.serializers import UserSerializer, UserProfileSerializer
from accounts.models import Customer, HotelManager, Admin
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class UserSerializerTests(TestCase):
    def test_user_serializer_validation(self):
        # Test password validation
        invalid_data = {
            'email': 'test@example.com',
            'name': 'Test',
            'last_name': 'User',
            'password': 'password123',
            'password2': 'password456',  # Different password
            'role': 'Customer'
        }
        
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        
        # Test valid data for customer
        valid_data = {
            'email': 'customer@example.com',
            'name': 'John',
            'last_name': 'Doe',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'Customer'
        }
        
        serializer = UserSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Test hotel manager validation
        hotel_manager_missing_data = {
            'email': 'manager@example.com',
            'name': 'Jane',
            'last_name': 'Smith',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'HotelManager'
            # Missing manager_profile data
        }
        
        serializer = UserSerializer(data=hotel_manager_missing_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('manager_profile', serializer.errors)
        
        # Test valid hotel manager data
        hotel_manager_valid_data = {
            'email': 'manager@example.com',
            'name': 'Jane',
            'last_name': 'Smith',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'HotelManager',
            'manager_profile': {
                'nationalID': 'ID123456789'
            }
        }
        
        serializer = UserSerializer(data=hotel_manager_valid_data)
        self.assertTrue(serializer.is_valid())
    
    def test_user_serializer_create(self):
        # Test creating a customer
        customer_data = {
            'email': 'customer@example.com',
            'name': 'John',
            'last_name': 'Doe',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'Customer'
        }
        
        serializer = UserSerializer(data=customer_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        self.assertEqual(user.email, 'customer@example.com')
        self.assertEqual(user.name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.role, 'Customer')
        self.assertTrue(hasattr(user, 'customer_profile'))
        self.assertTrue(user.customer_profile.customerID.startswith('CUST-'))
        
        # Test creating a hotel manager
        hotel_manager_data = {
            'email': 'manager@example.com',
            'name': 'Jane',
            'last_name': 'Smith',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'HotelManager',
            'manager_profile': {
                'nationalID': 'ID123456789',
                'verificationFile': SimpleUploadedFile("file.pdf", b"file_content")
            }
        }
        
        serializer = UserSerializer(data=hotel_manager_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        self.assertEqual(user.email, 'manager@example.com')
        self.assertEqual(user.role, 'HotelManager')
        self.assertTrue(hasattr(user, 'manager_profile'))
        self.assertTrue(user.manager_profile.managerID.startswith('MGR-'))
        self.assertEqual(user.manager_profile.nationalID, 'ID123456789')
        self.assertIsNotNone(user.manager_profile.verificationFile)

class UserProfileSerializerTests(TestCase):
    def setUp(self):
        # Create a user with customer profile
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test',
            last_name='User',
            role='Customer'
        )
        self.customer = Customer.objects.create(
            user=self.user,
            customerID='CUST-12345678'
        )
    
    def test_user_profile_serializer(self):
        serializer = UserProfileSerializer(instance=self.user)
        data = serializer.data
        
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
        self.assertEqual(data['role'], 'Customer')
        self.assertIn('customer_profile', data)
        self.assertEqual(data['customer_profile']['customerID'], 'CUST-12345678')