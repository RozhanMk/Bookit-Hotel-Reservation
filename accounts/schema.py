# accounts/schema.py
import graphene
from accounts.models import User, Customer, EmailVerificationCode
from accounts.serializers import UserSerializer, CustomerSerializer
from .utils import send_verification_email
from graphene_django.types import DjangoObjectType
from graphql import GraphQLError
from django.db import transaction


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'last_name', 'role', 'is_active', 'status']


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
            'role': 'Customer',
        }

        serializer = UserSerializer(data=user_data)
        if serializer.is_valid():
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    name=name,
                    last_name=last_name,
                    role='Customer',
                    password=password,
                    is_active=False  # email not verified yet
                )
                Customer.objects.create(user=user)
                verification = EmailVerificationCode.objects.create(user=user)
                send_verification_email(user, verification)

            return RegisterCustomer(user=user, message="Customer registered. Please verify your email.")
        else:
            raise GraphQLError(serializer.errors)

class VerifyEmail(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        code = graphene.String(required=True)

    message = graphene.String()

    def mutate(self, info, email, code):
        try:
            user = User.objects.get(email=email)
            verification = EmailVerificationCode.objects.get(user=user)

            if verification.is_verified:
                return VerifyEmail(message="Email already verified.")

            if verification.code != code:
                raise GraphQLError("Invalid verification code.")

            if verification.is_expired:
                raise GraphQLError("Verification code has expired.")

            verification.is_verified = True
            verification.save()

            user.is_active = True
            user.save()

            return VerifyEmail(message="Email verified successfully.")

        except User.DoesNotExist:
            raise GraphQLError("User not found.")
        except EmailVerificationCode.DoesNotExist:
            raise GraphQLError("Verification entry not found.")