from rest_framework import serializers
from hotel.models import Hotel, HotelFacility, Facility


class HotelSerializer(serializers.ModelSerializer):
    facilities = serializers.SlugRelatedField(
        many=True,
        queryset=HotelFacility.objects.all(),
        slug_field='facility_type',
        required=False
    )
    total_rooms = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = ['id', 'name', 'location', 'description', 'facilities',
                 'hotel_iban_number', 'rate', 'rate_number', 'hotel_license', 'image',
                 'status', 'discount', 'total_rooms']


    def get_total_rooms(self, obj):
        """Method to get the count of rooms for the hotel"""
        return obj.rooms.count()

    def create(self, validated_data):
        facilities = validated_data.pop('facilities', [])
        image = validated_data.get('image')
        hotel_license = validated_data.get('hotel_license')
        hotel_name = validated_data.get('name')
        hotel_manager = self.context['request'].user.hotelmanager  

        if image:
            image.name = f"{hotel_name.lower().replace(' ', '_')}_{hotel_manager.id}.png"
        if hotel_license:
            hotel_license.name = f"{hotel_name.lower().replace(' ', '_')}_{hotel_manager.id}.png"

        # Assign hotel_manager to validated_data before creation
        hotel = Hotel.objects.create(hotel_manager=hotel_manager, **validated_data)
        hotel.facilities.set(facilities)
        return hotel

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['facilities'] = [
            {
                'name': Facility(f.facility_type).label
            }
            for f in instance.facilities.all()
        ]
        return representation