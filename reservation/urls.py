from .views import ReservationViewSet
from django.urls import path


urlpatterns = [
    path('user/', ReservationViewSet.as_view({'patch': 'partial_update', 'get': 'retrieve'})),
    path('remove/', ReservationViewSet.as_view({'delete': 'destroy',})),
    path('create/', ReservationViewSet.as_view({'post': 'create',})),
    path('create/', ReservationViewSet.as_view({'get': 'list',})),
]