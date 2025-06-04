from django.db import models
from core.models import BaseModel
from room.models import Room
from accounts.models import Customer

class Reservation(BaseModel):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
    ]

    id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reservations')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    count_of_guests = models.PositiveIntegerField()
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
