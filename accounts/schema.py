import graphene
from graphene_django import DjangoObjectType
from accounts.models import User, Customer
from accounts.serializers import CustomerRegisterSerializer

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "email", "name", "last_name", "role")

class RegisterCustomer(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)
    message = graphene.String()

    def mutate(self, info, email, name, last_name, password):
        serializer = CustomerRegisterSerializer(data={
            "email": email,
            "name": name,
            "last_name": last_name,
            "password": password
        })
        if serializer.is_valid():
            user = serializer.save()
            Customer.objects.create(user=user)
            return RegisterCustomer(user=user, message="Customer registered successfully")
        else:
            raise Exception(serializer.errors)

class Mutation(graphene.ObjectType):
    register_customer = RegisterCustomer.Field()