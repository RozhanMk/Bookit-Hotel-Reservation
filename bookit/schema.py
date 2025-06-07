import graphene
from accounts.schema import RegisterHotelManager
from hotel.schema import CreateHotel

class Mutation(graphene.ObjectType):
    register_hotel_manager = RegisterHotelManager.Field()
    create_hotel = CreateHotel.Field()

schema = graphene.Schema(mutation=Mutation)