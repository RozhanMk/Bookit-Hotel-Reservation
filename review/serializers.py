from rest_framework import serializers
from .models import Review
from accounts.models import User

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id','user',  'user_name','user_last_name','user_email', 'hotel',  
            'hotel_name','good_thing','bad_thing','rating','created_at','updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['hotel', 'good_thing', 'bad_thing', 'rating']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
