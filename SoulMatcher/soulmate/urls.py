from rest_framework_simplejwt.views import TokenRefreshView

from rest_framework.routers import DefaultRouter

from django.urls import path, include

from . import views


router = DefaultRouter()
router.register(r'priorities', views.PriorityViewSet, basename='Priorities')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.register, name='register'),
    path('email-confirmation/<str:token>/', views.email_confirmation, name='email-confirmation'),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('temp_protected_view/', views.temp_protected_view, name='temp_protected_view'),
    path('compatible-users/<int:user_id>/', views.CompatibleUsersView.as_view(), name='compatible-users'),
]
