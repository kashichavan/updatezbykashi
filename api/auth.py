from ninja.security import HttpBearer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        jwt_authenticator = JWTAuthentication()
        try:
            # Authenticate the token. If successful, it returns (user, validated_token)
            validated_token = jwt_authenticator.get_validated_token(token)
            user = jwt_authenticator.get_user(validated_token)
            request.auth = validated_token # Store the validated token for potential later use
            return user
        except (InvalidToken, TokenError): # Catch specific JWT errors
            return None
        except Exception: # Catch any other unexpected errors
            return None

# Instance for use in NinjaAPI routers
auth_bearer = AuthBearer()

class OwnerAuthBearer(HttpBearer):
    """
    Enforces that the caller is authenticated AND possesses is_staff or is_superuser status.
    Blocks Broken Object Level Authorization (BOLA) and horizontal privilege escalation.
    """
    def authenticate(self, request, token):
        jwt_authenticator = JWTAuthentication()
        try:
            validated_token = jwt_authenticator.get_validated_token(token)
            user = jwt_authenticator.get_user(validated_token)
            if user and user.is_active and (user.is_staff or user.is_superuser):
                request.auth = validated_token
                return user
            return None
        except Exception:
            return None

owner_auth_bearer = OwnerAuthBearer()

