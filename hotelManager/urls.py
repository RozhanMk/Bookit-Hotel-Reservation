from bookit.urls import schema_view
from .views import HotelManagerViewSet, NoneAuthHotelManagerViewSet
from django.urls import path
from rest_framework import permissions


urlpatterns = [
    path('hotel-manager/', HotelManagerViewSet.as_view({'patch': 'partial_update', 'get': 'retrieve'})),
    path('get/', NoneAuthHotelManagerViewSet.as_view({'post': 'retrieve'})),
    path('remove/', HotelManagerViewSet.as_view({'delete': 'destroy',})),
    path('create/', NoneAuthHotelManagerViewSet.as_view({'post': 'create',})),
    path('list/', HotelManagerViewSet.as_view({'get': 'list',})),
]

