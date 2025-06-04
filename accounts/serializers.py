from rest_framework import serializers
from .models import User, Customer, Admin
from hotelManager.models import HotelManager
from django.contrib.auth.password_validation import validate_password


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer    # the model that it is based on
        fields = ['customerID']
        read_only_fields = ['customerID']

class HotelManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelManager
        fields = ['managerID', 'nationalID', 'verificationFile']
        read_only_fields = ['managerID']

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = ['adminID']
        read_only_fields = ['adminID']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    status = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'last_name', 'password','role','status']
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': False}
        }
    

    



