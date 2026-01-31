"""
Cache Middleware for Edge Caching
Story 3-8.18: Implement edge caching headers for CDN optimization

Adds appropriate cache headers to API responses:
- Static assets: Long cache (7 days)
- API responses: Short cache (5 minutes) with revalidation
- Search results: Very short cache (1 minute)
- User-specific: No caching
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers
from typing import Callable, Optional
import re


class CacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add cache headers for CDN edge caching

    Story 3-8.18: Optimizes CDN performance with appropriate cache policies
    """

    # URL patterns for different cache strategies
    CACHE_STRATEGIES = {
        # Static assets - long cache
        r'\.(js|css|png|jpg|jpeg|gif|svg|ico|webp|woff|woff2|ttf|eot)$': {
            'max_age': 60 * 60 * 24 * 7,  # 7 days
            'stale_while_revalidate': 60 * 60 * 24 * 30,  # 30 days
            'stale_if_error': 60 * 60 * 24 * 30,  # 30 days
            'public': True,
        },
        # API search endpoints - short cache
        r'^/api/(vehicles|search|semantic).*': {
            'max_age': 60,  # 1 minute
            'stale_while_revalidate': 300,  # 5 minutes
            'public': True,
        },
        # API recommendation endpoints - medium cache
        r'^/api/recommend.*': {
            'max_age': 300,  # 5 minutes
            'stale_while_revalidate': 600,  # 10 minutes
            'public': True,
        },
        # API conversation endpoints - no cache (user-specific)
        r'^/api/conversation.*': {
            'max_age': 0,
            'no_store': True,
            'private': True,
        },
        # API analytics - no cache
        r'^/api/analytics.*': {
            'max_age': 0,
            'no_store': True,
            'private': True,
        },
    }

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request and add cache headers to response

        Story 3-8.18: Adds Cache-Control and CDN headers
        """
        response = await call_next(request)

        # Get cache strategy for this request
        strategy = self._get_cache_strategy(request.url.path)

        if strategy:
            headers = self._build_cache_headers(strategy)

            # Add headers to response
            for key, value in headers.items():
                response.headers[key] = value

            # Add CDN-specific headers
            response.headers['X-Cache-Status'] = 'MISS'
            response.headers['X-Content-Type-Options'] = 'nosniff'

        return response

    def _get_cache_strategy(self, path: str) -> Optional[dict]:
        """
        Determine cache strategy based on URL path

        Story 3-8.18: Matches path against predefined strategies
        """
        for pattern, strategy in self.CACHE_STRATEGIES.items():
            if re.search(pattern, path):
                return strategy
        return None

    def _build_cache_headers(self, strategy: dict) -> dict:
        """
        Build Cache-Control header from strategy

        Story 3-8.18: Constructs CDN-compatible cache headers
        """
        directives = []

        if strategy.get('public'):
            directives.append('public')
        elif strategy.get('private'):
            directives.append('private')

        if strategy.get('no_store'):
            directives.append('no-store')

        max_age = strategy.get('max_age', 0)
        if max_age > 0:
            directives.append(f'max-age={max_age}')

        swr = strategy.get('stale_while_revalidate')
        if swr:
            directives.append(f'stale-while-revalidate={swr}')

        sie = strategy.get('stale_if_error')
        if sie:
            directives.append(f'stale-if-error={sie}')

        headers = {
            'Cache-Control': ', '.join(directives),
        }

        # Add Vary header for proper caching
        if not strategy.get('private'):
            headers['Vary'] = 'Accept-Encoding'

        return headers


def add_caching_headers_to_response(
    response: Response,
    max_age: int = 300,
    public: bool = True,
    stale_while_revalidate: Optional[int] = None,
) -> Response:
    """
    Helper function to add caching headers to a specific response

    Story 3-8.18: Can be used in endpoints for custom caching

    Args:
        response: The FastAPI response object
        max_age: Maximum cache time in seconds
        public: Whether response is public (True) or private (False)
        stale_while_revalidate: SWR time in seconds

    Returns:
        Response with cache headers added
    """
    directives = []

    if public:
        directives.append('public')
    else:
        directives.append('private')

    if max_age > 0:
        directives.append(f'max-age={max_age}')

    if stale_while_revalidate:
        directives.append(f'stale-while-revalidate={stale_while_revalidate}')

    response.headers['Cache-Control'] = ', '.join(directives)
    response.headers['Vary'] = 'Accept-Encoding'

    return response
