from .views import ReservationViewSet
from django.urls import path


urlpatterns = [
    path('all-hotel-reservations/', ReservationViewSet.as_view({'get': 'list'})),
    path('reservation/', ReservationViewSet.as_view({'get': 'retrieve'})),
    path('reserve/', ReservationViewSet.as_view({'post': 'reserve',})),
    path('lock-rooms/', ReservationViewSet.as_view({'post': 'lock_rooms_for_user',})),
    path('unlock-rooms/', ReservationViewSet.as_view({'post': 'unlock_rooms_for_user',})),
]
