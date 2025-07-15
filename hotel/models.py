from django.db import models
from core.models import BaseModel
from hotelManager.models import HotelManager
from django.core.validators import MinValueValidator, MaxValueValidator

class Facility(models.TextChoices):
    WIFI = "Wi-Fi", "Wi-Fi"
    PARKING = "Parking", "Parking"
    restaurant = "Restaurant", "Restaurant"
    coffeShop = "CoffeShop", "CoffeShop"
    roomService = "Room Service", "Room Service"
    laundryService = "Laundry Service", "Laundry Service"
    supportAgent = "Support Agent", "Support Agent"
    elevator = "Elevator", "Elevator"
    safeBox = "Safebox", "Safebox"
    tv = "TV", "TV"
    freeBreakFast = "FreeBreakFast", "FreeBreakFast"
    meetingRoom = "Meeting Room", "Meeting Room"
    childCare = "Child Care", "Child Care"
    POOL = "Pool", "Pool"
    GYM = "Gym", "Gym"
    taxi = "Taxi", "Taxi"
    pets_allowed = "Pets Allowed", "Pets Allowed"
    shoppingMall = "Shopping Mall", "Shopping Mall"


class Status(models.TextChoices):
    ACCEPTED = 'Accepted', 'Accepted'
    REJECTED = 'Rejected', 'Rejected'
    PENDING = 'Pending', 'Pending'

class DiscountStatus(models.TextChoices):
    ACTIVE = 'Active', 'Active'
    INACTIVE = 'Inactive', 'Inactive'
    EXPIRED = 'Expired', 'Expired'

class Hotel(BaseModel):

    hotel_manager = models.ForeignKey(HotelManager, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    location = models.TextField()
    description = models.TextField()
    image = models.ImageField(upload_to='hotel/images/')
    facilities = models.ManyToManyField('HotelFacility', blank=True)
    hotel_iban_number = models.CharField(max_length=24, blank=True)
    rate =  models.PositiveSmallIntegerField(default=0)
    rate_number = models.IntegerField(default=0)
    hotel_license = models.ImageField(upload_to='hotel/licenses/')
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
        help_text="Discount percentage (0-100)"
    )
    discount_status = models.CharField(
        max_length=10,
        choices=DiscountStatus.choices,
        default=DiscountStatus.INACTIVE
    )
    discount_start_date = models.DateTimeField(null=True, blank=True)
    discount_end_date = models.DateTimeField(null=True, blank=True)


class HotelFacility(models.Model):

    facility_type = models.CharField(max_length=65, choices=Facility.choices)

    def __str__(self):
        return self.facility_type
