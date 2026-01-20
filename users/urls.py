from django.urls import path
from .views import ChangePasswordView, RegisterView, LoginView, ForgotPasswordView, ResetPasswordView, RegisterAdminView, ProfileView

urlpatterns = [
    path("auth/register", RegisterView.as_view()),
    path("auth/register-admin", RegisterAdminView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/profile", ProfileView.as_view()),
    path("auth/forgot-password/", ForgotPasswordView.as_view()),
    path("auth/reset-password/<str:token>/", ResetPasswordView.as_view()),
    path("auth/change-password/", ChangePasswordView.as_view()),
]
