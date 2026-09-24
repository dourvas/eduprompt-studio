from django.conf import settings


class FrameAncestorsMiddleware:
    """
    Send a Content-Security-Policy frame-ancestors header on every response,
    and make sure no X-Frame-Options header is sent.

    Allowed framing origins: 'self' plus settings.FRAME_ANCESTORS (set through
    the FRAME_ANCESTORS environment variable, space-separated).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Tokens containing ';' or ',' are dropped so that an environment value
        # can never add a second directive or a second policy.
        origins = [
            origin for origin in getattr(settings, 'FRAME_ANCESTORS', [])
            if origin and ';' not in origin and ',' not in origin
        ]
        self.header_value = "frame-ancestors 'self' " + ' '.join(origins)
        self.header_value = self.header_value.strip()

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = self.header_value
        if 'X-Frame-Options' in response:
            del response['X-Frame-Options']
        return response
