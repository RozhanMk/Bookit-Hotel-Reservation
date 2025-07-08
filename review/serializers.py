from rest_framework import serializers
from .models import Review
from accounts.models import Customer

class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.name', read_only=True)
    customer_last_name = serializers.CharField(source='customer.user.last_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'customer', 'customer_name', 'customer_last_name', 'customer_email',
                 'hotel', 'hotel_name', 'good_thing', 'bad_thing', 'rating', 'created_at', 'updated_at']
        read_only_fields = ['customer', 'created_at', 'updated_at']

class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['hotel', 'good_thing', 'bad_thing', 'rating']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
