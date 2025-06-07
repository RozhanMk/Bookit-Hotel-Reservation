import graphene
from graphene_django.types import DjangoObjectType
from accounts.models import User
from hotelManager.models import HotelManager

class UserType(DjangoObjectType):
    class Meta:
        model = User

class HotelManagerType(DjangoObjectType):
    class Meta:
        model = HotelManager

class RegisterHotelManager(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        name = graphene.String(required=True)
        national_code = graphene.String(required=True)

    hotel_manager = graphene.Field(HotelManagerType)

    def mutate(self, info, email, password, name, national_code):
        user = User.objects.create_user(email=email, password=password, name=name, role="HotelManager")
        manager = HotelManager.objects.create(user=user, national_code=national_code)
        return RegisterHotelManager(hotel_manager=manager)
