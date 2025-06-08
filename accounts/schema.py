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
            error_messages = []
            for field, messages in serializer.errors.items():
                error_messages.extend([f"{field}: {msg}" for msg in messages])
            raise GraphQLError("\n".join(error_messages))

class VerifyEmailPayload(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    
class VerifyEmail(graphene.Mutation):
    Output = VerifyEmailPayload  # This tells GraphQL what fields to expect

    class Arguments:
        email = graphene.String(required=True)
        code = graphene.String(required=True)

    def mutate(self, info, email, code):
        try:
            verification = EmailVerificationCode.objects.get(user__email=email)
        except EmailVerificationCode.DoesNotExist:
            raise GraphQLError("No verification code found for this email.")

        if verification.is_verified:
            return VerifyEmailPayload(success=False, message="Email already verified.")

        if verification.is_expired:
            return VerifyEmailPayload(success=False, message="Verification code expired.")

        if verification.code != code:
            return VerifyEmailPayload(success=False, message="Invalid verification code.")

        verification.is_verified = True
        verification.save()

        verification.user.is_active = True
        verification.user.save()

        return VerifyEmailPayload(success=True, message="Email verified successfully.")
