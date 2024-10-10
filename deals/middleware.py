from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


class DisableCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    @method_decorator(never_cache)
    def __call__(self, request):
        response = self.get_response(request)
        return response
