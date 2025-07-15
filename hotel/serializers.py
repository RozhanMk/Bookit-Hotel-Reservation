from rest_framework import serializers
from hotel.models import Hotel, Facility
from django.utils import timezone
from .models import DiscountStatus


class HotelSerializer(serializers.ModelSerializer):

    facilities = serializers.CharField(source='facilities.name', read_only=True)
    total_rooms = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = ['id', 'name', 'location', 'description', 'facilities',
                 'hotel_iban_number', 'rate', 'rate_number', 'hotel_license', 'image',
                 'status', 'discount', 'total_rooms', 'discount_start_date', 'discount_end_date']


    def get_total_rooms(self, obj):
        """Method to get the count of rooms for the hotel"""
        return obj.rooms.count()



    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['facilities'] = [
            {
                'name': Facility(f.facility_type).label
            }
            for f in instance.facilities.all()
        ]
        return representation

class DiscountSerializer(serializers.Serializer):
    discount = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        required=True,
    )

    discount_start_date = serializers.DateTimeField(
        required=True,
    )

    discount_end_date = serializers.DateTimeField(
        required=True,
    )

    def validate(self, data):
        """
        Validate date ranges and discount status logic
        """
        errors = {}

        start_date = data.get('discount_start_date')
        end_date = data.get('discount_end_date')
        discount = data.get('discount', 0)

        if discount > 100 or discount < 0:
            errors['discount'] = "Discount must be between 0 and 100%"

        if start_date and end_date:
            if start_date >= end_date:
                errors['discount_end_date'] = "End date must be after start date"

            if start_date < timezone.now():
                errors['discount_start_date'] = "Start date cannot be in the past"


        if errors:
            raise serializers.ValidationError(errors)

        return data
