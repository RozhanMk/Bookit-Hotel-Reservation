from rest_framework import serializers
from hotelManager.models import HotelManager
from accounts.models import User

class UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'name', 'last_name', 'role']
        read_only_fields = ['role']

class HotelManagerSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer()

    class Meta:
        model = HotelManager
        fields = ['user', 'national_code', 'state']
        read_only_fields = ['state']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(
            email=user_data['email'],
            name=user_data['name'],
            last_name=user_data['last_name'],
            password=self.context['request'].data.get('password'),  # from raw request data
            role='Hotel Manager',
            is_active=False
        )
        manager = HotelManager.objects.create(user=user, **validated_data)
        return manager

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
