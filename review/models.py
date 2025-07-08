from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from hotel.models import Hotel  # assuming your hotel model is in hotel app
from accounts.models import Customer  # assuming your Customer model is in user app

class Review(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='reviews')
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reviews')
    good_thing = models.TextField(help_text="What did you like about this hotel?")
    bad_thing = models.TextField(help_text="What could be improved?")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rate from 1 to 5 stars"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Ensure one review per customer per hotel
        unique_together = ['customer', 'hotel']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.user.name} {self.customer.user.last_name} - {self.hotel.name} ({self.rating}/5)"