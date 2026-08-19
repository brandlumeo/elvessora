CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://checkout.razorpay.com; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
    "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com data:; "
    "img-src 'self' data: https:; "
    "connect-src 'self' https://api.razorpay.com https://lumberjack.razorpay.com; "
    "frame-src https://api.razorpay.com https://checkout.razorpay.com; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'self';"
)


class ContentSecurityPolicyMiddleware:
    """Adds a CSP header restricting script/style/frame/connect origins to self + known
    third parties (Bootstrap CDN, Google Fonts, Razorpay checkout). 'unsafe-inline' is kept
    for script/style because several templates use inline <script>/style="" attributes;
    tightening further would need those refactored to nonces/external files."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('Content-Security-Policy', CONTENT_SECURITY_POLICY)
        return response
