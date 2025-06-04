from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from .views import UserViewSet, AuthViewSet

urlpatterns = [
    # Auth endpoints
    path('register/', AuthViewSet.as_view({'post': 'register'}), name='register'),
    path('login/', AuthViewSet.as_view({'post': 'login'}), name='login'),
    path('verify-email/', AuthViewSet.as_view({'post': 'verify_email'}), name='verify_email'),
    path('resend-verification-code/', AuthViewSet.as_view({'post': 'resend_verification_code'}),
         name='resend_verification_code'),

    # JWT token endpoints
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # User profile endpoints
    path('users/profile/', UserViewSet.as_view({'get': 'profile', 'put': 'update_profile'}), name='user_profile'),
    path('logout/', UserViewSet.as_view({'post': 'logout'}), name='logout'),
]