from rest_framework import serializers
from hotelManager.models import HotelManager
from accounts.models import User

class HotelManagerSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    name = serializers.CharField(max_length=100, required=True)
    last_name = serializers.CharField(max_length=100, required=True)
    password = serializers.CharField(write_only=True)
    national_code = serializers.CharField(required=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value
