from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Customer, HotelManager, Admin

User = get_user_model()

class UserModelTests(TestCase):
    def test_create_user(self):
        email = 'test@example.com'
        password = 'testpass123'
        user = User.objects.create_user(
            email=email,
            password=password,
            name='Test',
            last_name='User'
        )
        
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.role, 'Customer')  # Default role
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
    
    def test_create_superuser(self):
        email = 'admin@example.com'
        password = 'adminpass123'
        admin_user = User.objects.create_superuser(
            email=email,
            password=password,
            name='Admin',
            last_name='User'
        )
        
        self.assertEqual(admin_user.email, email)
        self.assertTrue(admin_user.check_password(password))
        self.assertEqual(admin_user.name, 'Admin')
        self.assertEqual(admin_user.last_name, 'User')
        self.assertEqual(admin_user.role, 'Admin')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
    
    def test_email_normalized(self):
        email = 'test@EXAMPLE.COM'
        user = User.objects.create_user(
            email=email,
            password='test123',
            name='Test',
            last_name='User'
        )
        self.assertEqual(user.email, email.lower())

class CustomerModelTests(TestCase):
    def test_customer_creation(self):
        user = User.objects.create_user(
            email='customer@example.com',
            password='pass123',
            name='John',
            last_name='Doe',
            role='Customer'
        )
        
        customer = Customer.objects.create(
            user=user,
            customerID='CUST-12345678'
        )
        
        self.assertEqual(customer.user, user)
        self.assertEqual(customer.customerID, 'CUST-12345678')
        self.assertEqual(str(customer), 'John Doe')

class HotelManagerModelTests(TestCase):
    def test_hotel_manager_creation(self):
        user = User.objects.create_user(
            email='manager@example.com',
            password='pass123',
            name='Jane',
            last_name='Smith',
            role='HotelManager'
        )
        
        manager = HotelManager.objects.create(
            user=user,
            managerID='MGR-12345678',
            nationalID='ID123456789'
        )
        
        self.assertEqual(manager.user, user)
        self.assertEqual(manager.managerID, 'MGR-12345678')
        self.assertEqual(manager.nationalID, 'ID123456789')
        self.assertEqual(str(manager), 'Jane Smith')

class AdminModelTests(TestCase):
    def test_admin_creation(self):
        user = User.objects.create_user(
            email='sysadmin@example.com',
            password='pass123',
            name='Alex',
            last_name='Johnson',
            role='Admin'
        )
        
        admin = Admin.objects.create(
            user=user,
            adminID='ADM-12345678'
        )
        
        self.assertEqual(admin.user, user)
        self.assertEqual(admin.adminID, 'ADM-12345678')
        self.assertEqual(str(admin), 'Alex Johnson')