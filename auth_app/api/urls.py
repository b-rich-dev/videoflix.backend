from django.urls import path
from .views import RegisterView, ActivateAccountView, CookieLoginView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),
    path('login/', CookieLoginView.as_view(), name='login'),
]