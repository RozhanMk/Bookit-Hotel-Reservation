from .views import HotelViewSet, FacilitySeederViewSet
from django.urls import path


urlpatterns = [
    path('hotel/', HotelViewSet.as_view({'get': 'my_hotels', 'post': 'create'})),  # List user's hotels & create
    path('hotel/<int:pk>/', HotelViewSet.as_view({
        'get': 'retrieve',            
        'patch': 'partial_update',    
        'delete': 'destroy'           
    })),
    path('all-hotels/', HotelViewSet.as_view({'get': 'list'})),  # List all accepted hotels (public)
    path('add-fac/', FacilitySeederViewSet.as_view({'post': 'create_fac'})),
    path('hotels/by-location/', HotelViewSet.as_view({'get': 'hotels_by_location'})),
    path('hotels/with-discount/', HotelViewSet.as_view({'get': 'hotels_with_discount'})),
    path('hotels/top-rated/', HotelViewSet.as_view({'get': 'top_rated_hotels'})),
]