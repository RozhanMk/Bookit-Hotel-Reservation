from bookit.urls import schema_view
from .views import HotelManagerViewSet, NoneAuthHotelManagerViewSet
from django.urls import path

urlpatterns = [
    # Authenticated hotel manager endpoints
    path('hotel-manager/', HotelManagerViewSet.as_view({
        'get': 'retrieve',  # Get current manager's profile
        'patch': 'partial_update'  # Update current manager's profile
    })),

    path('list/', HotelManagerViewSet.as_view({
        'get': 'list'  # List all hotel managers (admin function)
    })),

    path('remove/', HotelManagerViewSet.as_view({
        'delete': 'destroy'  # Delete current manager's account
    })),

    # Non-authenticated endpoints
    path('create/', NoneAuthHotelManagerViewSet.as_view({
        'post': 'create'  # Register new hotel manager
    })),

    path('login/', NoneAuthHotelManagerViewSet.as_view({
        'post': 'retrieve'  # Login hotel manager
    })),

    path('hotel_manager/monthly_reservations/', HotelManagerViewSet.as_view({
        'get': 'monthly_reservations'  # Login hotel manager
    })),

    path('hotel_manager/reservation_stats/', HotelManagerViewSet.as_view({
        'post': 'reservation_stats'  # Login hotel manager
    })),
    
    path('hotel_manager/activate_discount/', HotelManagerViewSet.as_view({
        'post': 'set_discount_on_hotel'  # Login hotel manager
    })),
    path('hotel_manager/hotel-reservations/', HotelManagerViewSet.as_view({
        'get': 'list_reservations_of_hotels'
    })),
]
