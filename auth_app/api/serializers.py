from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Handles user account creation with password confirmation and email validation.
    """
    
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def validate_confirmed_password(self, value):
        password = self.initial_data.get('password')
        if value and password and password != value:
            raise serializers.ValidationError("Passwords do not match.")
        return value
    
    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Email is required.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value
    
    def save(self):
        pw = self.validated_data['password']
        
        account = User(
            email=self.validated_data['email'],
            username=self.validated_data['email'],
            is_active=False
        )
        account.set_password(pw)
        account.save()
        return account
    

