from hotelManager.serializers import HotelManagerSerializer


list_hotel_managers_docs = {
    'operation_description': """
    Retrieve a list of all hotel managers.

    Requires authentication.

    Returns:
    - 200: Success, returns list of hotel managers
    - 404: If no hotel managers are found
    """,
    'responses': {
        200: HotelManagerSerializer(many=True),
        404: {
            'description': 'Hotel managers not found',
            'content': {
                'application/json': {
                    'example': {'error': 'hotel manager not found'}
                }
            }
        }
    }
}

retrieve_hotel_manager_docs = {
    'operation_description': """
    Retrieve a specific hotel manager by email and password (login).

    Does not require authentication.

    Parameters:
    - email: The email of the hotel manager
    - password: The password of the hotel manager

    Returns:
    - 200: Success, returns hotel manager data with access token
    - 404: If hotel manager or user is not found
    """,
    'request_body': {
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'email': {'type': 'string', 'format': 'email'},
                        'password': {'type': 'string'}
                    },
                    'required': ['email', 'password']
                }
            }
        }
    },
    'responses': {
        200: {
            'description': 'Hotel manager data with access token',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'data': HotelManagerSerializer(),
                            'access': {'type': 'string'}
                        }
                    }
                }
            }
        },
        404: {
            'description': 'Hotel manager or user not found',
            'content': {
                'application/json': {
                    'examples': {
                        'manager_not_found': {'value': {'error': 'hotel manager not found'}},
                        'user_not_found': {'value': {'error': 'user does not exist'}}
                    }
                }
            }
        }
    }
}

update_hotel_manager_docs = {
    'operation_description': """
    Partially update the authenticated hotel manager's information.

    Requires authentication.
    Only updates fields provided in the request.

    Returns:
    - 200: Success, returns updated hotel manager data
    - 400: If validation errors occur
    - 404: If hotel manager is not found
    """,
    'request_body': {
        'content': {
            'application/json': {
                'schema': HotelManagerSerializer()
            }
        }
    },
    'responses': {
        200: {
            'description': 'Updated hotel manager data',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'data': HotelManagerSerializer()
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Validation errors',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'errors': {'type': 'object'}
                        }
                    }
                }
            }
        },
        404: {
            'description': 'Hotel manager not found',
            'content': {
                'application/json': {
                    'example': {'error': 'hotel manager not found'}
                }
            }
        }
    }
}

register_hotel_manager_docs = {
    'operation_description': """
    Register a new hotel manager.

    Does not require authentication.
    Creates a new user with Hotel Manager role (initially inactive).
    Sends verification email with OTP code.

    Required fields:
    - email
    - name
    - last_name
    - national_code
    - password

    Returns:
    - 201: Success, returns created hotel manager data
    - 400: If validation errors occur or hotel manager already exists
    """,
    'request_body': {
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'email': {'type': 'string', 'format': 'email'},
                        'name': {'type': 'string'},
                        'last_name': {'type': 'string'},
                        'national_code': {'type': 'string'},
                        'password': {'type': 'string'}
                    },
                    'required': ['email', 'name', 'last_name', 'national_code', 'password']
                }
            }
        }
    },
    'responses': {
        201: {
            'description': 'Hotel manager created (inactive)',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'data': HotelManagerSerializer(),
                            'message': {'type': 'string'}
                        }
                    },
                    'example': {
                        'data': HotelManagerSerializer(),
                        'message': 'hotel manager created not active enter otp code'
                    }
                }
            }
        },
        400: {
            'description': 'Validation errors or hotel manager exists',
            'content': {
                'application/json': {
                    'examples': {
                        'validation_error': {'value': {'errors': {}}},
                        'manager_exists': {'value': {'error': 'hotel manager exists'}}
                    }
                }
            }
        }
    }
}

# For the destroy method (though it's empty in your code)
destroy_hotel_manager_docs = {
    'operation_description': """
    Delete a hotel manager account.

    Requires authentication.
    This will permanently delete the hotel manager's account.

    Returns:
    - 204: Success, no content
    """,
    'responses': {
        204: {
            'description': 'Hotel manager deleted successfully',
            'content': None
        }
    }
}