from django.urls import path
from .views import review_list_create, review_detail, hotel_review_stats, user_hotel_review

app_name = 'review'

urlpatterns = [
    path('hotels/<int:hotel_id>/', review_list_create, name='review-list-create'),
    path('review/<int:pk>/', review_detail, name='review-detail'),
    path('hotels/<int:hotel_id>/stats/', hotel_review_stats, name='hotel-review-stats'),
    path('hotels/<int:hotel_id>/user/', user_hotel_review, name='user-hotel-review'),
]