from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from hotel.models import Hotel  # assuming your hotel model is in hotel app
from accounts.models import User  # assuming your Customer model is in user app

class Review(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='reviews')
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, related_name='reviews')
    good_thing = models.TextField(help_text='What did you like about this hotel?')
    bad_thing = models.TextField(help_text='What could be improved?')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rate from 1 to 5 stars'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'hotel')  # ✅ FIXED HERE
