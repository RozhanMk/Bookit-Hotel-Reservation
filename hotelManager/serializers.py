from rest_framework import serializers

class HotelManagerSerializer(serializers.Serializer):

    name = serializers.CharField(source='user.name'  ,max_length=100, required=True)
    last_name = serializers.CharField(source='user.last_name'  ,max_length=100, required=True)
    email = serializers.EmailField(source='user.email'  ,required=True)
    role = serializers.CharField(source='user.role' ,max_length=30, read_only=True)
    national_code = serializers.CharField(required=True)
    state = serializers.CharField(read_only=True)



