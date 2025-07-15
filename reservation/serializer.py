from rest_framework import serializers
from .models import Reservation, Payment
from room.models import Room
from hotel.models import Hotel
from accounts.models import Customer

class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = ['id', 'name', 'location','image', 'discount_start_date', 'discount_end_date']

class RoomSerializer(serializers.ModelSerializer):
    hotel = HotelSerializer(read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id', 
            'hotel',
            'room_number',
            'room_type',
            'price',
            'image'
        ]

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'amount',
            'method',
            'status',
        ]
        read_only_fields = ['id']

class ReservationSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())
    room_details = RoomSerializer(source='room', read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), required=False)

    class Meta:
        model = Reservation
        fields = [
            'id',
            'room',
            'room_details',
            'user',
            'check_in_date',
            'check_out_date',
            'status',
        ]
        read_only_fields = [
            'id', 
            'status',
            'room_details'
        ]

    def validate(self, data):
        """
        Validate reservation dates and guest count
        """
        if data['check_in_date'] >= data['check_out_date']:
            raise serializers.ValidationError("Check-out date must be after check-in date")

        room = data['room']
        if data.get('count_of_guests', 1) > room.capacity:
            raise serializers.ValidationError(
                f"Room capacity exceeded. Maximum {room.capacity} guests allowed."
            )

        return data

class ReservationDetailSerializer(ReservationSerializer):
    """
    Extended serializer with nested payment and detailed room information
    """
    payments = PaymentSerializer(many=True, read_only=True)
    hotel = serializers.SerializerMethodField()

    class Meta(ReservationSerializer.Meta):
        fields = ReservationSerializer.Meta.fields + ['payments', 'hotel']

    def get_hotel(self, obj):
        return HotelSerializer(obj.room.hotel).data

class PaymentDetailSerializer(PaymentSerializer):
    """
    Extended payment serializer with reservation details
    """
    reservation_details = serializers.SerializerMethodField()

    class Meta(PaymentSerializer.Meta):
        fields = PaymentSerializer.Meta.fields + ['reservation_details']

    def get_reservation_details(self, obj):
        return {
            'check_in_date': obj.reservation.check_in_date,
            'check_out_date': obj.reservation.check_out_date,
            'room_number': obj.reservation.room.room_number,
            'hotel_name': obj.reservation.room.hotel.name
        }
