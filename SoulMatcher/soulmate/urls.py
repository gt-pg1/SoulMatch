from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('email-confirmation/<str:token>/', views.email_confirmation, name='email-confirmation'),
]
