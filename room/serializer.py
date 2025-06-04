# serializers.py
from rest_framework import serializers
from hotel.models import Hotel
from room.models import Room, RoomType, DiscountStatus
from hotel.serializers import HotelSerializer


class RoomSerializer(serializers.ModelSerializer):
    room_type = serializers.ChoiceField(choices=RoomType.choices)
    discounted_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    hotel = serializers.PrimaryKeyRelatedField(queryset=Hotel.objects.all())

    class Meta:
        model = Room
        fields = ['id','hotel','name','room_type','price','image','rate','rate_number','discounted_price',
        ]
        read_only_fields = ['rate', 'rate_number']

    def create(self, validated_data):
        image = validated_data.get('image')
        hotel = validated_data.get('hotel')
        room_name = validated_data.get('name')

        # Customize image name
        if image:
            image.name = f"{hotel.id}_{room_name.lower().replace(' ', '_')}.png"

        return super().create(validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['hotel'] = HotelSerializer(instance.hotel).data
        return representation