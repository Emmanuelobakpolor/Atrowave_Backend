from django.urls import path
from .views import RegisterView, LoginView, ForgotPasswordView, ResetPasswordView

urlpatterns = [
    path("auth/register", RegisterView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/forgot-password/", ForgotPasswordView.as_view()),
    path("auth/reset-password/<str:token>/", ResetPasswordView.as_view()),
]
