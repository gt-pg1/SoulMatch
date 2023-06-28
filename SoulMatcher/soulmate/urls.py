from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('email-confirmation/<str:token>/', views.email_confirmation, name='email-confirmation'),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('temp_protected_view/', views.temp_protected_view, name='temp_protected_view'),
]
