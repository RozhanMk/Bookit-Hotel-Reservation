from .views import RoomViewSet
from django.urls import path

urlpatterns = [
    path('room/', RoomViewSet.as_view({'patch': 'partial_update'})),
    path('room/<int:pk>/', RoomViewSet.as_view({'get': 'retrieve'})),
    path('remove/<int:pk>/', RoomViewSet.as_view({'delete': 'destroy'})),
    path('create/', RoomViewSet.as_view({'post': 'create'})),
    path('all-rooms/', RoomViewSet.as_view({'post': 'list'})),
]