from django.db import models
from .manager import BaseManager


class BaseModel(models.Model):
    objects = BaseManager()
    create_datetime = models.DateTimeField(auto_now_add=True, editable=False)
    modify_datetime = models.DateTimeField(auto_now=True, editable=False)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)


    objects = BaseManager()

    class Meta:

        abstract = True


    def active(self):
        self.is_active = True
        self.save()

    def deactivate(self):
        self.is_active = False
        self.save()