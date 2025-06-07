# hotel/schema.py
import graphene
from graphene_file_upload.scalars import Upload
from hotel.models import Hotel, HotelFacility
from hotel.serializers import HotelSerializer
from graphene_django.types import DjangoObjectType

class HotelType(DjangoObjectType):
    class Meta:
        model = Hotel
        fields = '__all__'

class CreateHotel(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        location = graphene.String(required=True)
        description = graphene.String(required=False)
        hotel_iban_number = graphene.String(required=False)
        hotel_license = Upload(required=False)
        image = Upload(required=False)
        facilities = graphene.List(graphene.String)  # facility_type names like ["WIFI", "TV"]
        discount = graphene.Float(required=False)

    hotel = graphene.Field(HotelType)
    message = graphene.String()

    def mutate(self, info, name, location, facilities=None, description=None,
               hotel_iban_number=None, image=None, hotel_license=None, discount=0.0):

        user = info.context.user
        if not hasattr(user, 'hotelmanager'):
            raise Exception("Only hotel managers can create hotels.")

        data = {
            'name': name,
            'location': location,
            'description': description,
            'hotel_iban_number': hotel_iban_number,
            'discount': discount,
            'facilities': facilities or [],
            'image': image,
            'hotel_license': hotel_license
        }

        serializer = HotelSerializer(data=data, context={'request': info.context})
        if serializer.is_valid():
            hotel = serializer.save()
            return CreateHotel(hotel=hotel, message="Hotel created successfully.")
        else:
            raise Exception(serializer.errors)
