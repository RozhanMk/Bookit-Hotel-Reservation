from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('hotel/<int:hotel_id>/', views.ReviewListCreateView.as_view(), name='hotel-reviews'),
    
    # Get hotel review statistics
    path('hotel/<int:hotel_id>/stats/', views.hotel_review_stats, name='hotel-review-stats'),
    
    # Get current user's review for a hotel
    path('hotel/<int:hotel_id>/my-review/', views.user_hotel_review, name='user-hotel-review'),
    
    # Update/delete a specific review
    path('<int:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
]