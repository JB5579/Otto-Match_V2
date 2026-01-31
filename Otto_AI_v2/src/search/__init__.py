"""
Otto.AI Search Package

Contains intelligent filtering and advanced RAG search functionality.

Story References:
- 1-4: Intelligent Vehicle Filtering (FilterService)
- 1-9: Hybrid Search with FTS (HybridSearchService)
- 1-10: Query Expansion Service (QueryExpansionService)
- 1-11: Re-ranking Layer (RerankingService)
- 1-12: Contextual Embeddings (ContextualEmbeddingService)
"""

from .filter_service import IntelligentFilterService

# RAG Strategy Services (Stories 1-9 through 1-12)
from .query_expansion_service import QueryExpansionService, QueryExpansion
from .hybrid_search_service import HybridSearchService, HybridSearchResult, HybridSearchResponse
from .reranking_service import RerankingService, RerankResult
from .contextual_embedding_service import ContextualEmbeddingService
from .search_orchestrator import SearchOrchestrator, SearchRequest, SearchResponse, SearchResult

__all__ = [
    # Original filtering
    'IntelligentFilterService',

    # Query expansion
    'QueryExpansionService',
    'QueryExpansion',

    # Hybrid search
    'HybridSearchService',
    'HybridSearchResult',
    'HybridSearchResponse',

    # Re-ranking
    'RerankingService',
    'RerankResult',

    # Contextual embeddings
    'ContextualEmbeddingService',

    # Orchestrator
    'SearchOrchestrator',
    'SearchRequest',
    'SearchResponse',
    'SearchResult',
]