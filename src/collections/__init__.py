"""
Otto.AI Collections Package

Contains vehicle collection management and trending algorithms.
"""

from .collection_engine import (
    CollectionEngine,
    Collection,
    CollectionCriteria,
    CollectionTemplate,
    CollectionType,
    ScoringFactor
)

__all__ = [
    'CollectionEngine',
    'Collection',
    'CollectionCriteria',
    'CollectionTemplate',
    'CollectionType',
    'ScoringFactor'
]