from bookit.urls import schema_view
from .views import HotelManagerViewSet, NoneAuthHotelManagerViewSet
from django.urls import path

urlpatterns = [
    path('hotel-managers/', HotelManagerViewSet.as_view({
        'get': 'list',
    })),
    path('hotel-managers/profile/', HotelManagerViewSet.as_view({
        'get': 'get_profile',
        'patch': 'partial_update',
    })),
    # Your non-auth endpoints
    path('register/', NoneAuthHotelManagerViewSet.as_view({'post': 'create'})),
    path('login/', NoneAuthHotelManagerViewSet.as_view({'post': 'retrieve'})),
]