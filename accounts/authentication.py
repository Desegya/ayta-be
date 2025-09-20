from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def get_raw_token(self, header):
        # Try to get token from Authorization header first
        if header is not None:
            return super().get_raw_token(header)
        # If not present, get from cookies
        request = self.request
        return request.COOKIES.get('access_token')
    
    def authenticate(self, request):
        self.request = request  # Save request for get_raw_token
        header = self.get_header(request)
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token