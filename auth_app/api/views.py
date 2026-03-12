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
from .tokens import generate_token
from .permissions import IsActive

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
                subject='Bestätige deine E-Mail @ Videoflix',
                message=f'Hallo {user.email.split("@")[0]},\n\nBitte bestätige deine E-Mail: {activation_link}',
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
    