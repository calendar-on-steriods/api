"""
Serializers for the user API View.
"""
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import jwt
import time


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""

    MINIMUM_IAT_AGE_PWD_CHANGE = 60

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update and return user."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            request = self.context.get('request')
            if self.is_auth_recent(request):
                user.set_password(password)
                user.save()
            else:
                msg = _('Authorization needed')
                raise serializers.ValidationError(msg, code='authorization')

        return user

    def is_auth_recent(self, request):
        try:
            auth = request.auth
            iat = jwt.decode(str(auth), options={
                "verify_signature": False})['iat']

            token_age = time.time() - iat

            return token_age < self.MINIMUM_IAT_AGE_PWD_CHANGE
        except Exception:
            return False


class CreatePairSerializer(TokenObtainPairSerializer):
    """Get JWT token pairs."""

    def validate(self, attr):
        try:
            data = super().validate(attr)
            refresh = self.get_token(self.user)
            data['refresh'] = str(refresh)
            data['access'] = str(refresh.access_token)

            return data

        except Exception:
            msg = _('Unable to authenticate with provided credentials.')
            raise serializers.ValidationError(msg, code='authorization')
