from rest_framework import serializers

class HotelManagerSerializer(serializers.Serializer):

    name = serializers.CharField(source='user.name'  ,max_length=100, required=True)
    last_name = serializers.CharField(source='user.last_name'  ,max_length=100, required=True)
    email = serializers.EmailField(source='user.email'  ,required=True)
    role = serializers.CharField(source='user.role' ,max_length=30, read_only=True)
    national_code = serializers.CharField(required=True)
    state = serializers.CharField(read_only=True)


from rest_framework import serializers
from reservation.models import Reservation, Payment, Room, User
from hotel.models import Hotel


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'last_name', 'email', 'role']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['amount', 'method', 'status']


class ReservationSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    payments = PaymentSerializer(read_only=True)
    room_number = serializers.SerializerMethodField()
    room_type = serializers.SerializerMethodField()
    room_name = serializers.SerializerMethodField()
    hotel_name = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id',
            'user',
            'room_number',
            'room_type',
            'room_name',
            'hotel_name',
            'check_in_date',
            'check_out_date',
            'status',
            'payments',
        ]

    def get_room_number(self, obj):
        return obj.room.room_number

    def get_room_type(self, obj):
        return obj.room.room_type

    def get_room_name(self, obj):
        return obj.room.name

    def get_hotel_name(self, obj):
        return obj.room.hotel.name


class HotelReservationsSerializer(serializers.ModelSerializer):
    reservations = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = ['id', 'name', 'location','reservations', 'discount_start_date', 'discount_end_date']

    def get_reservations(self, obj):
        rooms = Room.objects.filter(hotel=obj)
        reservations = Reservation.objects.filter(room__in=rooms).select_related(
            'user', 'room', 'room__hotel'
        ).prefetch_related('payments')

        return ReservationSerializer(reservations, many=True).data


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = [
            'discount',
            'discount_status',
            'discount_start_date',
            'discount_end_date'
        ]
    
    def validate_discount(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Discount must be between 0 and 100 percent")
        return value
    
    def validate(self, data):
        """
        Validate that:
        1. If discount_status is Active, both dates must be present
        2. End date must be after start date
        3. Dates must be in the future when setting discount
        """
        discount_status = data.get('discount_status', self.instance.discount_status if self.instance else None)
        start_date = data.get('discount_start_date')
        end_date = data.get('discount_end_date')
        
        if discount_status == Hotel.DiscountStatus.ACTIVE:
            if not start_date or not end_date:
                raise serializers.ValidationError("Both start and end dates are required for active discount")
            
            if start_date >= end_date:
                raise serializers.ValidationError("Discount end date must be after start date")
            
            now = timezone.now()
            if start_date < now:
                raise serializers.ValidationError("Discount start date must be in the future")
        
        return data



