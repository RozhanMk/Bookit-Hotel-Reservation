from bookit.urls import schema_view
from .views import HotelManagerViewSet, NoneAuthHotelManagerViewSet
from django.urls import path

urlpatterns = [
    path('hotel-managers/', HotelManagerViewSet.as_view({
        'get': 'list',
    })),
    path('hotel-managers/<int:pk>/', HotelManagerViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
    path('hotel-managers/profile/', HotelManagerViewSet.as_view({
        'get': 'get_profile'  
    })),
    # Your non-auth endpoints
    path('register/', NoneAuthHotelManagerViewSet.as_view({'post': 'create'})),
    path('login/', NoneAuthHotelManagerViewSet.as_view({'post': 'retrieve'})),
]