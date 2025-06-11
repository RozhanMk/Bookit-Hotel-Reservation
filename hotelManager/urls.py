from bookit.urls import schema_view
from .views import HotelManagerViewSet, NoneAuthHotelManagerViewSet
from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


urlpatterns = [
    # Authenticated Hotel Manager actions
    path('hotel-manager/', HotelManagerViewSet.as_view({
        'patch': 'partial_update',
    }), name='hotel-manager-update'),

    path('delete/', HotelManagerViewSet.as_view({
        'delete': 'destroy',
    }), name='hotel-manager-delete'),

    path('hotel-managers/', HotelManagerViewSet.as_view({
        'get': 'list',
    }), name='hotel-manager-list'),

    # Unauthenticated actions
    path('register/', NoneAuthHotelManagerViewSet.as_view({
        'post': 'create',
    }), name='hotel-manager-register'),

    path('login/', NoneAuthHotelManagerViewSet.as_view({
        'post': 'retrieve',  
    }), name='hotel-manager-login'),
]