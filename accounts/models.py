from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
import random
import string
from django.utils import timezone
from datetime import timedelta
from .manager import UserManager
from core.models import BaseModel



class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    ROLE_CHOICES = (
        ('Customer', 'Customer'),
        ('HotelManager', 'Hotel Manager'),
        ('Admin', 'Admin'),
    )
    
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, default='')
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='Customer')
    is_staff = models.BooleanField(default=False)
    favorite_hotels = models.ManyToManyField(
        'hotel.Hotel',
        blank=True,
        related_name='favorited_by',
        help_text='Hotels that this user has marked as favorites'
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'last_name']
    
    def __str__(self):
        return self.email

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    
    def __str__(self):
        return f"{self.user.name} {self.user.last_name}"


class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    
    def __str__(self):
        return f"{self.user.name} {self.user.last_name}"


class EmailVerificationCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {'Verified' if self.is_verified else 'Not Verified'}"

    def save(self, *args, **kwargs):
        # Set expiration time (30 minutes from creation)
        if not self.id:
            self.expires_at = timezone.now() + timedelta(minutes=30)
            # Generate a random 6-digit code
            self.code = ''.join(random.choices(string.digits, k=4))
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
