from django.urls import path

from .views import LoginView, RegistrationView, VerifyOTPView

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
]
