from urllib.parse import urlsplit

from django.conf import settings
from django.http import JsonResponse


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


class SameOriginPostMiddleware:
    """
    Cross-site guard that needs no cookie (replaces CSRF protection).

    For any request that is not GET/HEAD/OPTIONS/TRACE: if the browser sent an
    Origin header, its host (and port) must equal the host this request was
    addressed to, as computed by request.get_host(). The scheme is not compared:
    TLS is terminated by the hosting proxy, so the app may see http while the
    browser used https. A request without an Origin header (non-browser caller)
    is allowed. Origin "null" is rejected.
    """

    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS', 'TRACE')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in self.SAFE_METHODS:
            origin = request.headers.get('Origin')
            if origin is not None and not self._same_host(origin, request):
                return JsonResponse(
                    {"error": "Cross-site request rejected"}, status=403
                )
        return self.get_response(request)

    @staticmethod
    def _same_host(origin, request):
        parts = urlsplit(origin)
        if parts.scheme not in ('http', 'https') or not parts.netloc:
            return False
        return parts.netloc.lower() == request.get_host().lower()
