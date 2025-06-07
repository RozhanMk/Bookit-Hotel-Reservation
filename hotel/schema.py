import graphene
from graphene_django.types import DjangoObjectType
from hotel.models import Hotel
from hotelManager.models import HotelManager

class HotelType(DjangoObjectType):
    class Meta:
        model = Hotel

class CreateHotel(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        location = graphene.String(required=True)
        description = graphene.String(required=True)

    hotel = graphene.Field(HotelType)

    def mutate(self, info, name, location, description):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Authentication required")
        try:
            manager = HotelManager.objects.get(user=user)
        except HotelManager.DoesNotExist:
            raise Exception("You are not a hotel manager")
        
        hotel = Hotel.objects.create(
            name=name,
            location=location,
            description=description,
            hotel_manager=manager
        )
        return CreateHotel(hotel=hotel)
