"""
Otto.AI API Package

Contains REST API endpoints and request handlers.
"""

from .semantic_search_api import app as semantic_search_app
# Temporarily disabled - has import errors in recommendation module
# from .vehicle_comparison_api import app as comparison_app
# from .filter_management_api import app as filter_app
from .listings_api import listings_router

__all__ = [
    'semantic_search_app',
    # 'comparison_app',
    # 'filter_app',
    'listings_router'
]