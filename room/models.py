from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import BaseModel
from hotel.models import Hotel
from accounts.models import User


class RoomType(models.TextChoices):
    SINGLE = 'Single', 'Single'
    DOUBLE = 'Double', 'Double'
    TRIPLE = 'Triple', 'Triple'


class DiscountStatus(models.TextChoices):
    ACTIVE = 'Active', 'Active'
    INACTIVE = 'Inactive', 'Inactive'
    EXPIRED = 'Expired', 'Expired'


class Room(BaseModel):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.IntegerField()
    name = models.CharField(max_length=120)
    room_type = models.CharField(max_length=15, choices=RoomType.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='room/images/')
    rate = models.PositiveSmallIntegerField(default=0)
    rate_number = models.IntegerField(default=0)


    class Meta:
        ordering = ['hotel', 'room_type', 'price']

    def __str__(self):
        return f"{self.hotel.name} - {self.name} Room"

    @property
    def discounted_price(self):
        """Calculate the price after applying discount"""
        if self.hotel.discount_status == DiscountStatus.ACTIVE and self.hotel.discount > 0:
            discount_amount = (self.price * self.hotel.discount) / 100
            return self.price - discount_amount
        return self.price

    def apply_discount(self, discount_percentage):
        """Apply discount to the room"""
        if 0 <= discount_percentage <= 100:
            self.hotel.discount = discount_percentage
            self.hotel.discount_status = DiscountStatus.ACTIVE
            self.save()

    def remove_discount(self):
        """Remove discount from the room"""
        self.hotel.discount = 0
        self.hotel.discount_status = DiscountStatus.INACTIVE
        self.save()


class RoomLock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    locked_until = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'room')
