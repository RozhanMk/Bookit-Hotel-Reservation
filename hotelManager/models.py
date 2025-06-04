from django.db import models

from core.models import BaseModel
from accounts.models import User

class Status(models.TextChoices):
    ACCEPTED = 'Accepted', 'Accepted'
    REJECTED = 'Rejected', 'Rejected'
    PENDING = 'Pending', 'Pending'


class HotelManager(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    national_code = models.CharField(max_length=10, unique=True)
    verificationFile = models.FileField(upload_to='hotel-manager/verificationFiles/', null=True, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)


    def __str__(self):
        return str(self.id)



