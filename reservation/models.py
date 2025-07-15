from django.db import models
from core.models import BaseModel
from room.models import Room
from accounts.models import User

class Reservation(BaseModel):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reservation')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')


class Payment(BaseModel):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
    ]
    METHOD_CHOICES = [
        ('In person', 'In person'),
        ('online', 'online'),
    ]
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='payments')
    amount = models.PositiveIntegerField()
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
