"""
Views for the user API.
"""
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response
from rest_framework import status

from users.serializers import (
    UserSerializer,
    CreatePairSerializer,
)


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer


class RefreshTokenView(TokenRefreshView):
    """Create refresh user JWT token."""

    def post(self, request, *args, **kwargs):
        """Handle token refresh."""
        if 'refresh' in self.request.COOKIES:
            if hasattr(request.data, '_mutable'):
                request.data._mutable = True
            request.data['refresh'] \
                = self.request.COOKIES['refresh']

        res = super().post(request, *args, **kwargs)
        res.set_cookie(
            'access', res.data['access'], httponly=True)

        return res


class CreateTokenView(TokenObtainPairView):
    """Create a new auth token for the user"""
    serializer_class = CreatePairSerializer

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        res = Response(serializer.validated_data,
                       status=status.HTTP_200_OK)
        res.set_cookie(
            'refresh', serializer.validated_data['refresh'], httponly=True)

        res.set_cookie(
            'access', serializer.validated_data['access'], httponly=True)

        return res


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user
