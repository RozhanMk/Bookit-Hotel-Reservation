import graphene
from accounts.schema import RegisterHotelManager
from hotel.schema import CreateHotel

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")

class Mutation(graphene.ObjectType):
    register_hotel_manager = RegisterHotelManager.Field()
    create_hotel = CreateHotel.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)