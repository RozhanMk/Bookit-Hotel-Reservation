from rest_framework import serializers
from accounts.models import User
from hotelManager.models import HotelManager

class HotelManagerCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    name = serializers.CharField(source='user.name')
    last_name = serializers.CharField(source='user.last_name')
    password = serializers.CharField(source='user.password', write_only=True)

    class Meta:
        model = HotelManager
        fields = ['email', 'name', 'last_name', 'password', 'national_code']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(
            email=user_data['email'],
            name=user_data['name'],
            last_name=user_data['last_name'],
            password=user_data['password'],
            role="Hotel Manager",
            is_active=False
        )
        hotel_manager = HotelManager.objects.create(user=user, **validated_data)
        return hotel_manager

class HotelManagerSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = HotelManager
        fields = ['id', 'email', 'name', 'last_name', 'national_code', 'status']
        read_only_fields = ['id', 'status']