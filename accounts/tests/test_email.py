from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from django.core import mail
from datetime import datetime, timedelta
from accounts.models import User, EmailVerificationCode

class EmailVerificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.registration_url = reverse('register')  
        self.verify_email_url = reverse('verify_email')
        self.resend_code_url = reverse('resend_verification_code')
        
        self.user_data = {
            'email': 'test@example.com',
            'name': 'Test',
            'last_name': 'User',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
            'role': 'Customer'
        }

    def test_user_registration_creates_verification_code(self):
        response = self.client.post(self.registration_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check user was created
        user = User.objects.get(email='test@example.com')
        self.assertFalse(user.is_active)  # User should not be active yet
        
        # Check verification code was created
        verification = EmailVerificationCode.objects.get(user=user)
        self.assertIsNotNone(verification.code)
        self.assertFalse(verification.is_verified)
        self.assertEqual(len(verification.code), 6)  

    def test_email_is_sent_on_registration(self):
        response = self.client.post(self.registration_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your Hotel Reservation Account Verification Code')
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        
        # Check that the code is in the email
        user = User.objects.get(email='test@example.com')
        verification = EmailVerificationCode.objects.get(user=user)
        self.assertIn(verification.code, mail.outbox[0].body)

    def test_verification_success(self):
        # First register a user
        response = self.client.post(self.registration_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Get the verification code
        user = User.objects.get(email='test@example.com')
        verification = EmailVerificationCode.objects.get(user=user)
        
        # Verify the email
        verification_data = {
            'email': 'test@example.com',
            'verification_code': verification.code
        }
        response = self.client.post(self.verify_email_url, verification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that user is now active and verification is marked as verified
        user.refresh_from_db()
        verification.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(verification.is_verified)

    def test_verification_invalid_code(self):
        # First register a user
        response = self.client.post(self.registration_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to verify with wrong code
        verification_data = {
            'email': 'test@example.com',
            'verification_code': '000000'  # Wrong code
        }
        response = self.client.post(self.verify_email_url, verification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that user is still not active
        user = User.objects.get(email='test@example.com')
        self.assertFalse(user.is_active)

    def test_verification_expired_code(self):
        """Test verification with expired code"""
        # First register a user
        response = self.client.post(self.registration_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Make the code expired
        user = User.objects.get(email='test@example.com')
        verification = EmailVerificationCode.objects.get(user=user)
        verification.expires_at = datetime.now() - timedelta(minutes=1)
        verification.save()
        
        # Try to verify
        verification_data = {
            'email': 'test@example.com',
            'verification_code': verification.code
        }
        response = self.client.post(self.verify_email_url, verification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that user is still not active
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_resend_verification_code(self):
        # First register a user
        response = self.client.post(self.registration_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Get the original code
        user = User.objects.get(email='test@example.com')
        original_verification = EmailVerificationCode.objects.get(user=user)
        original_code = original_verification.code
        
        # Clear the email outbox
        mail.outbox = []
        
        resend_data = {
            'email': 'test@example.com'
        }
        response = self.client.post(self.resend_code_url, resend_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that a new email was sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Check that a new code was generated
        new_verification = EmailVerificationCode.objects.get(user=user)
        new_code = new_verification.code
        self.assertNotEqual(original_code, new_code)
        
        # Check that the new code is in the email
        self.assertIn(new_code, mail.outbox[0].body)

    def test_resend_for_already_verified_user(self):
        # First register a user
        response = self.client.post(self.registration_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the user
        user = User.objects.get(email='test@example.com')
        verification = EmailVerificationCode.objects.get(user=user)
        verification.is_verified = True
        verification.save()
        user.is_active = True
        user.save()
        
        # Clear the email outbox
        mail.outbox = []
        
        # Try to resend the code
        resend_data = {
            'email': 'test@example.com'
        }
        response = self.client.post(self.resend_code_url, resend_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that no email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_for_nonexistent_user(self):
        resend_data = {
            'email': 'nonexistent@example.com'
        }
        response = self.client.post(self.resend_code_url, resend_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_already_verified_user(self):
        # First register a user
        response = self.client.post(self.registration_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the user
        user = User.objects.get(email='test@example.com')
        verification = EmailVerificationCode.objects.get(user=user)
        verification_code = verification.code
        verification.is_verified = True
        verification.save()
        user.is_active = True
        user.save()
        
        # Try to verify again
        verification_data = {
            'email': 'test@example.com',
            'verification_code': verification_code
        }
        response = self.client.post(self.verify_email_url, verification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('django.core.mail.EmailMessage.send')
    def test_email_sending_failure(self, mock_send):
        # Make the email sending fail
        mock_send.side_effect = Exception("Failed to send email")
        
        # Try to register
        with self.assertRaises(Exception):
            response = self.client.post(self.registration_url, self.user_data, format='json')
            
        # Check that no user was created (due to transaction.atomic)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(EmailVerificationCode.objects.count(), 0)