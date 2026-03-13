from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer
from .tokens import generate_token, password_reset_token

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class RegisterView(APIView):
    """
    API view for user registration.
    Allows any user to create a new account with email, and password.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = generate_token.make_token(user)
            activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}"
            message = render_to_string('auth_app/activation_email.html', {
                'name': user.email.split('@')[0],
                'activation_link': activation_link,
            })
            send_mail(
                subject='Confirm your email @ Videoflix',
                message=f'Hello {user.email.split("@")[0]},\n\nPlease confirm your email: {activation_link}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=message,
                fail_silently=False,
            )
            return Response(
                {
                    'user': {
                        'id': user.id,
                        'email': user.email,
                    },
                    'token': token,
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and generate_token.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({'message': 'Account successfully activated.'}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid or expired activation link.'}, status=status.HTTP_400_BAD_REQUEST)
   
    
class CookieLoginView(TokenObtainPairView):
    """
    API view for user login with JWT tokens stored in HTTP-only cookies.
    Returns access and refresh tokens in secure cookies along with user data.
    """
    
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh_token = response.data.get('refresh')
        access_token = response.data.get('access')
        user_data = response.data.get('user')
        
        response.set_cookie(
            key='access', 
            value=access_token, 
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        
        response.set_cookie(
            key='refresh', 
            value=refresh_token, 
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        
        response.data = {'detail': "Login successful", 'user': user_data}
        
        return response


class LogoutView(APIView):
    """
    API view for user logout.
    Blacklists the refresh token and deletes authentication cookies for authenticated users.
    """
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        
        response = Response({"detail": "Log-Out successful! All tokens will be deleted. Refresh token is now invalid."}, status=status.HTTP_200_OK)
        response.delete_cookie('access', samesite='Lax')
        response.delete_cookie('refresh', samesite='Lax')
        return response
   

class CookieTokenRefreshView(TokenRefreshView):
    """
    API view for refreshing JWT tokens stored in HTTP-only cookies.
    Returns a new access token in a secure cookie if the refresh token is valid.
    """

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')
        
        if refresh_token is None:
            return Response({'detail': 'Refresh token not found.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data={'refresh': refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        access_token = serializer.validated_data['access']
        
        response = Response({'detail': 'Token refreshed', 'access': access_token}, status=status.HTTP_200_OK)
        response.set_cookie(
            key='access', 
            value=access_token, 
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        
        return response


class PasswordResetView(APIView):
    """
    API view for initiating password reset process.
    Accepts an email address, generates a password reset token, and sends a reset link via email.
    """
    
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'If an account with that email exists, a password reset link has been sent.'}, status=status.HTTP_200_OK)
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/password-reset/{uid}/{token}"
        message = render_to_string('auth_app/password_reset_email.html', {
            'name': user.email.split('@')[0],
            'reset_link': reset_link,
        })
        send_mail(
            subject='Reset password @ Videoflix',
            message=f'Hello {user.email.split("@")[0]},\n\nPlease click the following link to reset your password: {reset_link}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=message,
            fail_silently=False,
        )
        
        return Response({'detail': 'An email has been sent to reset your password.'}, status=status.HTTP_200_OK)    


class PasswordResetConfirmView(APIView):
    """
    API view for confirming password reset.
    Validates the token and allows the user to set a new password.
    """
    
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not password_reset_token.check_token(user, token):
            return Response({'detail': 'Invalid or expired reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({'detail': 'Account is not active.'}, status=status.HTTP_400_BAD_REQUEST)
        
        new_password = request.data.get('new_password')
        confirmed_password = request.data.get('confirm_password')
        
        if not new_password or not confirmed_password:
            return Response({'detail': 'New password and confirmed password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirmed_password:
            return Response({'detail': 'New password and confirmed password do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        
        return Response({'detail': 'Your Password has been successfully reset.'}, status=status.HTTP_200_OK)
    