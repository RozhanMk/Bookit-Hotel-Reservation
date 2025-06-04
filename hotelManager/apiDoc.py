from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Common response schemas
not_found_response = openapi.Response(
    description="Not Found",
    examples={
        "application/json": {
            "error": "hotel manager not found"
        }
    }
)

bad_request_response = openapi.Response(
    description="Bad Request",
    examples={
        "application/json": {
            "errors": {
                "field_name": ["Error message"]
            }
        }
    }
)

# Hotel Manager Schemas
hotel_manager_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'user': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'role': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        # Add other HotelManager fields here
    }
)

# Hotel Manager Registration Schema
registration_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email', 'name', 'last_name', 'password'],
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
        'name': openapi.Schema(type=openapi.TYPE_STRING),
        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
        'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD),
        # Add other registration fields here
    }
)

# Decorators for each endpoint
list_hotel_managers_docs = swagger_auto_schema(
    operation_description="Retrieve a list of all hotel managers (admin only)",
    responses={
        200: openapi.Response(
            description="List of hotel managers",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=hotel_manager_schema
            )
        ),
        404: not_found_response,
    },
    security=[{"Bearer": []}]
)

retrieve_hotel_manager_docs = swagger_auto_schema(
    operation_description="Retrieve the profile of the authenticated hotel manager",
    responses={
        200: openapi.Response(
            description="Hotel manager details",
            schema=hotel_manager_schema
        ),
        404: not_found_response,
    },
    security=[{"Bearer": []}]
)

update_hotel_manager_docs = swagger_auto_schema(
    operation_description="Update the profile of the authenticated hotel manager",
    request_body=hotel_manager_schema,
    responses={
        200: openapi.Response(
            description="Hotel manager updated successfully",
            schema=hotel_manager_schema
        ),
        400: bad_request_response,
        404: not_found_response,
    },
    security=[{"Bearer": []}]
)

register_hotel_manager_docs = swagger_auto_schema(
    operation_description="Create a new hotel manager account",
    request_body=registration_schema,
    responses={
        201: openapi.Response(
            description="Hotel manager created successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                            'name': openapi.Schema(type=openapi.TYPE_STRING),
                            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'role': openapi.Schema(type=openapi.TYPE_STRING),
                            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        }
                    ),
                    'hotel-manager': hotel_manager_schema,
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: bad_request_response,
    }
)