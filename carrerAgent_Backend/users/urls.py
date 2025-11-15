from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, ProfileView, ChangePasswordView, DeleteUserView, UserDetailView, UpdateProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("delete/", DeleteUserView.as_view(), name="delete-user"),
    path("self/", UserDetailView.as_view(), name="user-detail"),
    path("update/", UpdateProfileView.as_view(), name="update-profile"),
]
