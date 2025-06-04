from django.db import models



class BaseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_delete=False)

    def get_all(self):
        return super().get_queryset().filter(is_delete=False)