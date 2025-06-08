# accounts/schema.py
import graphene
from accounts.models import User, Customer, EmailVerificationCode
from accounts.serializers import UserSerializer, CustomerSerializer
from graphene_django.types import DjangoObjectType
from graphql import GraphQLError
from django.utils import timezone

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'last_name', 'role']

class RegisterCustomer(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)
    message = graphene.String()

    def mutate(self, info, email, name, last_name, password):
        user_data = {
            'email': email,
            'name': name,
            'last_name': last_name,
            'password': password,
            'role': 'Customer'
        }

        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            user.set_password(password)
            user.save()
            Customer.objects.create(user=user)
            return RegisterCustomer(user=user, message="Customer registered successfully.")
        else:
            raise Exception(user_serializer.errors)

class VerifyEmail(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        email = graphene.String(required=True)
        code = graphene.String(required=True)

    def mutate(self, info, email, code):
        try:
            verification = EmailVerificationCode.objects.select_related('user').get(user__email=email)
        except EmailVerificationCode.DoesNotExist:
            raise GraphQLError("Verification entry not found for this email.")

        if verification.is_verified:
            return VerifyEmail(success=False, message="Email is already verified.")

        if verification.code != code:
            return VerifyEmail(success=False, message="Invalid verification code.")

        if verification.is_expired:
            return VerifyEmail(success=False, message="Verification code has expired.")

        verification.is_verified = True
        verification.save()
        return VerifyEmail(success=True, message="Email verified successfully.")
