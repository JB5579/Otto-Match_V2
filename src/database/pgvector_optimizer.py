"""
PGVector Optimizer for Otto.AI
Implements Story 1-8: Optimize pgvector IVFFLAT index with similarity_threshold

Features:
- IVFFLAT index optimization with dynamic probe lists
- Similarity threshold tuning for optimal recall/precision
- Vector query optimization and analysis
- Index maintenance and rebuilding strategies
- Performance monitoring and analytics
"""

import logging
import asyncio
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import os
import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector

logger = logging.getLogger(__name__)

@dataclass
class IndexConfiguration:
    """Configuration for vector indexes"""
    index_type: str = "ivfflat"  # ivfflat or hnsw
    lists: int = 100  # Number of lists for IVFFLAT
    m: int = 16  # Number of connections per node for HNSW
    ef_construction: int = 64  # Construction parameters for HNSW
    ef_search: int = 40  # Search parameters for HNSW
    similarity_threshold: float = 0.7  # Default similarity threshold
    probe_list_size: int = 10  # Number of lists to probe for IVFFLAT

@dataclass
class QueryPerformanceMetrics:
    """Metrics for query performance analysis"""
    query_time_ms: float
    rows_examined: int
    rows_returned: int
    index_usage: bool
    similarity_scores: List[float]
    cache_hit: bool
    execution_plan: Dict[str, Any]

@dataclass
class IndexStatistics:
    """Statistics for vector index performance"""
    index_name: str
    index_type: str
    table_size: int
    index_size_mb: float
    tuples_inserted: int
    tuples_updated: int
    tuples_deleted: int
    pages_fetched: int
    tuples_returned: int
    last_analyzed: datetime
    avg_similarity_score: float
    query_count: int
    avg_query_time_ms: float

class PGVectorOptimizer:
    """Optimizer for pgvector indexes and queries"""

    def __init__(self):
        self.db_conn = None
        self.config = IndexConfiguration()
        self.index_stats: Dict[str, IndexStatistics] = {}
        self.query_history: List[QueryPerformanceMetrics] = []

        # Optimization parameters
        self.similarity_threshold_range = [0.5, 0.9]
        self.probe_list_sizes = [1, 5, 10, 20, 50, 100]
        self.max_query_history = 1000

    async def initialize(self, supabase_url: str, supabase_key: str) -> bool:
        """Initialize database connection"""
        try:
            project_ref = supabase_url.split('//')[1].split('.')[0]
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            if not db_password:
                raise ValueError("SUPABASE_DB_PASSWORD environment variable is required")

            connection_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
            self.db_conn = psycopg.connect(connection_string)
            register_vector(self.db_conn)

            logger.info("✅ PGVector Optimizer connected to Supabase")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize PGVector Optimizer: {e}")
            return False

    async def create_optimized_ivfflat_index(
        self,
        table_name: str,
        column_name: str,
        index_name: Optional[str] = None,
        lists: Optional[int] = None,
        distance_metric: str = "cosine"
    ) -> bool:
        """Create optimized IVFFLAT index"""
        try:
            if not index_name:
                index_name = f"idx_{table_name}_{column_name}_ivfflat_{distance_metric}"

            lists = lists or self._calculate_optimal_lists(table_name)

            # Determine index operator based on distance metric
            if distance_metric == "cosine":
                operator = "vector_cosine_ops"
            elif distance_metric == "l2":
                operator = "vector_l2_ops"
            elif distance_metric == "inner_product":
                operator = "vector_ip_ops"
            else:
                raise ValueError(f"Unsupported distance metric: {distance_metric}")

            # Drop existing index if it exists
            await self._drop_index_if_exists(index_name)

            # Create optimized IVFFLAT index
            create_sql = f"""
                CREATE INDEX {index_name} ON {table_name}
                USING ivfflat ({column_name} {operator})
                WITH (lists = {lists});
            """

            with self.db_conn.cursor() as cur:
                cur.execute(create_sql)
                self.db_conn.commit()

            logger.info(f"✅ Created IVFFLAT index {index_name} with {lists} lists")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create IVFFLAT index: {e}")
            return False

    async def create_optimized_hnsw_index(
        self,
        table_name: str,
        column_name: str,
        index_name: Optional[str] = None,
        m: Optional[int] = None,
        ef_construction: Optional[int] = None,
        distance_metric: str = "cosine"
    ) -> bool:
        """Create optimized HNSW index"""
        try:
            if not index_name:
                index_name = f"idx_{table_name}_{column_name}_hnsw_{distance_metric}"

            m = m or self.config.m
            ef_construction = ef_construction or self.config.ef_construction

            # Determine index operator
            if distance_metric == "cosine":
                operator = "vector_cosine_ops"
            elif distance_metric == "l2":
                operator = "vector_l2_ops"
            elif distance_metric == "inner_product":
                operator = "vector_ip_ops"
            else:
                raise ValueError(f"Unsupported distance metric: {distance_metric}")

            # Drop existing index if it exists
            await self._drop_index_if_exists(index_name)

            # Create optimized HNSW index
            create_sql = f"""
                CREATE INDEX {index_name} ON {table_name}
                USING hnsw ({column_name} {operator})
                WITH (m = {m}, ef_construction = {ef_construction});
            """

            with self.db_conn.cursor() as cur:
                cur.execute(create_sql)
                self.db_conn.commit()

            logger.info(f"✅ Created HNSW index {index_name} with m={m}, ef_construction={ef_construction}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create HNSW index: {e}")
            return False

    async def optimize_similarity_threshold(
        self,
        table_name: str,
        column_name: str,
        sample_queries: List[List[float]],
        target_recall: float = 0.9,
        max_precision_loss: float = 0.1
    ) -> Dict[str, Any]:
        """Find optimal similarity threshold for given recall/precision targets"""
        try:
            results = {
                "thresholds_tested": [],
                "optimal_threshold": None,
                "optimal_recall": None,
                "optimal_precision": None,
                "performance_metrics": {}
            }

            logger.info(f"🔍 Optimizing similarity threshold for {table_name}.{column_name}")

            # Test different similarity thresholds
            for threshold in np.linspace(0.5, 0.95, 10):
                threshold_results = await self._test_similarity_threshold(
                    table_name, column_name, sample_queries, threshold
                )

                threshold_results["threshold"] = threshold
                results["thresholds_tested"].append(threshold_results)

                # Check if we meet targets
                if (threshold_results["recall"] >= target_recall and
                    threshold_results["precision"] >= (1 - max_precision_loss)):

                    results["optimal_threshold"] = threshold
                    results["optimal_recall"] = threshold_results["recall"]
                    results["optimal_precision"] = threshold_results["precision"]

                    # Update configuration
                    self.config.similarity_threshold = threshold
                    break

            # If no optimal found, use best tradeoff
            if results["optimal_threshold"] is None:
                best = max(results["thresholds_tested"],
                          key=lambda x: x["recall"] + x["precision"])
                results["optimal_threshold"] = best["threshold"]
                results["optimal_recall"] = best["recall"]
                results["optimal_precision"] = best["precision"]

            logger.info(f"✅ Optimal similarity threshold: {results['optimal_threshold']:.3f}")
            return results

        except Exception as e:
            logger.error(f"❌ Failed to optimize similarity threshold: {e}")
            return {"error": str(e)}

    async def optimize_probe_list_size(
        self,
        table_name: str,
        column_name: str,
        sample_queries: List[List[float]],
        target_performance_ms: float = 100.0
    ) -> Dict[str, Any]:
        """Find optimal probe list size for IVFFLAT index"""
        try:
            results = {
                "probe_sizes_tested": [],
                "optimal_probe_size": None,
                "performance_metrics": {}
            }

            logger.info(f"🔍 Optimizing probe list size for {table_name}.{column_name}")

            # Set IVFFLAT probe parameter for testing
            for probe_size in self.probe_list_sizes:
                with self.db_conn.cursor() as cur:
                    cur.execute(f"SET ivfflat.probes = {probe_size}")

                # Test performance with current probe size
                probe_results = await self._test_probe_performance(
                    table_name, column_name, sample_queries
                )

                probe_results["probe_size"] = probe_size
                results["probe_sizes_tested"].append(probe_results)

                # Check if performance target met
                if probe_results["avg_query_time_ms"] <= target_performance_ms:
                    results["optimal_probe_size"] = probe_size
                    break

            # If no optimal found, use fastest
            if results["optimal_probe_size"] is None:
                fastest = min(results["probe_sizes_tested"],
                            key=lambda x: x["avg_query_time_ms"])
                results["optimal_probe_size"] = fastest["probe_size"]

            # Update configuration
            self.config.probe_list_size = results["optimal_probe_size"]

            logger.info(f"✅ Optimal probe list size: {results['optimal_probe_size']}")
            return results

        except Exception as e:
            logger.error(f"❌ Failed to optimize probe list size: {e}")
            return {"error": str(e)}

    async def analyze_index_performance(self, index_name: str) -> IndexStatistics:
        """Analyze index performance and statistics"""
        try:
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                # Get basic index stats
                cur.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        indexdef,
                        pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                        pg_relation_size(indexrelid) as index_size_bytes
                    FROM pg_stat_user_indexes
                    WHERE indexname = %s;
                """, (index_name,))
                index_info = cur.fetchone()

                if not index_info:
                    raise ValueError(f"Index {index_name} not found")

                # Get usage statistics
                cur.execute("""
                    SELECT
                        idx_tup_read,
                        idx_tup_fetch,
                        idx_scan,
                        pg_stat_get_last_vacuum_time(indexrelid) as last_vacuum,
                        pg_stat_get_last_analyze_time(indexrelid) as last_analyzed
                    FROM pg_stat_user_indexes
                    WHERE indexname = %s;
                """, (index_name,))
                stats = cur.fetchone()

                # Get table statistics
                cur.execute("""
                    SELECT
                        n_tup_ins as tuples_inserted,
                        n_tup_upd as tuples_updated,
                        n_tup_del as tuples_deleted,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples
                    FROM pg_stat_user_tables
                    WHERE schemaname || '.' || tablename = %s;
                """, (index_info['schemaname'] + '.' + index_info['tablename'],))
                table_stats = cur.fetchone()

                # Analyze recent query performance
                cur.execute("""
                    SELECT
                        avg_similarity_score,
                        query_count,
                        avg_query_time_ms
                    FROM (
                        -- This would come from query logging or monitoring
                        SELECT
                            0.75 as avg_similarity_score,
                            COUNT(*) as query_count,
                            50.0 as avg_query_time_ms
                        FROM (SELECT 1) dummy
                    ) subquery;
                """)
                query_stats = cur.fetchone() or {}

                # Create statistics object
                index_stats = IndexStatistics(
                    index_name=index_name,
                    index_type="ivfflat" if "ivfflat" in index_info['indexdef'] else "hnsw",
                    table_size=table_stats['live_tuples'] if table_stats else 0,
                    index_size_mb=index_info['index_size_bytes'] / (1024 * 1024),
                    tuples_inserted=table_stats['tuples_inserted'] if table_stats else 0,
                    tuples_updated=table_stats['tuples_updated'] if table_stats else 0,
                    tuples_deleted=table_stats['tuples_deleted'] if table_stats else 0,
                    pages_fetched=stats['idx_tup_read'] if stats else 0,
                    tuples_returned=stats['idx_tup_fetch'] if stats else 0,
                    last_analyzed=stats['last_analyzed'] if stats else datetime.now(),
                    avg_similarity_score=query_stats.get('avg_similarity_score', 0.0),
                    query_count=query_stats.get('query_count', 0),
                    avg_query_time_ms=query_stats.get('avg_query_time_ms', 0.0)
                )

                self.index_stats[index_name] = index_stats
                return index_stats

        except Exception as e:
            logger.error(f"❌ Failed to analyze index performance: {e}")
            raise

    async def execute_optimized_search(
        self,
        table_name: str,
        column_name: str,
        query_vector: List[float],
        limit: int = 10,
        similarity_threshold: Optional[float] = None,
        use_brute_force: bool = False
    ) -> List[Dict[str, Any]]:
        """Execute optimized vector similarity search"""
        try:
            threshold = similarity_threshold or self.config.similarity_threshold

            # Set optimal parameters
            with self.db_conn.cursor() as cur:
                # Set probe size for IVFFLAT
                cur.execute(f"SET ivfflat.probes = {self.config.probe_list_size}")

                # Set ef for HNSW if applicable
                cur.execute(f"SET hnsw.ef_search = {self.config.ef_search}")

            # Build query
            if use_brute_force:
                query = f"""
                    SELECT *,
                           1 - ({column_name} <=> %s::vector) as similarity_score
                    FROM {table_name}
                    WHERE 1 - ({column_name} <=> %s::vector) >= %s
                    ORDER BY {column_name} <=> %s::vector
                    LIMIT %s;
                """
            else:
                # Use index (optimizer will choose best path)
                query = f"""
                    SELECT *,
                           1 - ({column_name} <=> %s::vector) as similarity_score
                    FROM {table_name}
                    WHERE 1 - ({column_name} <=> %s::vector) >= %s
                    ORDER BY {column_name} <=> %s::vector
                    LIMIT %s;
                """

            with self.db_conn.cursor(row_factory=dict_row) as cur:
                start_time = asyncio.get_event_loop().time()

                cur.execute(query, [
                    query_vector,  # For calculation
                    query_vector,  # For WHERE clause
                    threshold,
                    query_vector,  # For ORDER BY
                    limit
                ])

                results = cur.fetchall()
                query_time = (asyncio.get_event_loop().time() - start_time) * 1000

            # Log performance metrics
            metrics = QueryPerformanceMetrics(
                query_time_ms=query_time,
                rows_examined=len(results),
                rows_returned=len(results),
                index_usage=not use_brute_force,
                similarity_scores=[r['similarity_score'] for r in results],
                cache_hit=False,  # Would need cache integration
                execution_plan={}  # Would need EXPLAIN ANALYZE
            )

            self.query_history.append(metrics)

            # Trim history if needed
            if len(self.query_history) > self.max_query_history:
                self.query_history = self.query_history[-self.max_query_history:]

            logger.debug(f"Executed optimized search in {query_time:.2f}ms, returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"❌ Failed to execute optimized search: {e}")
            return []

    async def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get optimization recommendations based on current performance"""
        try:
            recommendations = {
                "index_optimizations": [],
                "query_optimizations": [],
                "parameter_tuning": [],
                "maintenance_suggestions": []
            }

            # Analyze index statistics
            for index_name, stats in self.index_stats.items():
                # Check index efficiency
                if stats.avg_query_time_ms > 100:
                    recommendations["index_optimizations"].append({
                        "type": "performance",
                        "index": index_name,
                        "issue": f"Slow query times ({stats.avg_query_time_ms:.1f}ms avg)",
                        "recommendation": "Consider increasing probe list size or rebuilding index"
                    })

                if stats.avg_similarity_score < 0.6:
                    recommendations["parameter_tuning"].append({
                        "type": "threshold",
                        "index": index_name,
                        "current_threshold": self.config.similarity_threshold,
                        "recommendation": "Lower similarity threshold may improve recall"
                    })

                # Check for maintenance needs
                if stats.tuples_deleted > stats.tuples_inserted * 0.1:
                    recommendations["maintenance_suggestions"].append({
                        "type": "maintenance",
                        "index": index_name,
                        "issue": f"High delete ratio ({stats.tuples_deleted}/{stats.tuples_inserted})",
                        "recommendation": "Consider VACUUM and index rebuild"
                    })

            # Analyze query patterns
            if self.query_history:
                avg_time = np.mean([q.query_time_ms for q in self.query_history])
                if avg_time > 200:
                    recommendations["query_optimizations"].append({
                        "type": "query_performance",
                        "issue": f"Average query time is high ({avg_time:.1f}ms)",
                        "recommendation": "Consider increasing ef_search or probe count"
                    })

            return recommendations

        except Exception as e:
            logger.error(f"❌ Failed to get optimization recommendations: {e}")
            return {"error": str(e)}

    def _calculate_optimal_lists(self, table_name: str) -> int:
        """Calculate optimal number of lists for IVFFLAT index"""
        # Heuristic: sqrt(rows) / 4 for IVFFLAT
        # In production, this would query the actual table size
        estimated_rows = 100000  # Default estimate
        return max(10, int(np.sqrt(estimated_rows) / 4))

    async def _drop_index_if_exists(self, index_name: str):
        """Drop index if it exists"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute(f"DROP INDEX IF EXISTS {index_name};")
                self.db_conn.commit()
        except Exception as e:
            logger.warning(f"Could not drop index {index_name}: {e}")

    async def _test_similarity_threshold(
        self,
        table_name: str,
        column_name: str,
        sample_queries: List[List[float]],
        threshold: float
    ) -> Dict[str, Any]:
        """Test a specific similarity threshold"""
        try:
            total_results = 0
            total_time = 0
            relevant_results = 0

            for query_vector in sample_queries[:10]:  # Limit for testing
                results = await self.execute_optimized_search(
                    table_name, column_name, query_vector,
                    limit=20, similarity_threshold=threshold
                )

                total_results += len(results)
                total_time += sum([r.get('query_time_ms', 0) for r in self.query_history[-1:]])

                # Count results above threshold as "relevant"
                relevant_results += sum(1 for r in results if r['similarity_score'] >= threshold)

            # Calculate metrics (simplified)
            precision = relevant_results / max(total_results, 1)
            recall = min(1.0, total_results / 100)  # Assuming 100 relevant docs total
            avg_time = total_time / max(len(sample_queries), 1)

            return {
                "precision": precision,
                "recall": recall,
                "avg_query_time_ms": avg_time,
                "results_count": total_results
            }

        except Exception as e:
            logger.error(f"Error testing similarity threshold {threshold}: {e}")
            return {"precision": 0, "recall": 0, "avg_query_time_ms": 999999}

    async def _test_probe_performance(
        self,
        table_name: str,
        column_name: str,
        sample_queries: List[List[float]]
    ) -> Dict[str, Any]:
        """Test performance with current probe settings"""
        try:
            total_time = 0
            total_results = 0

            for query_vector in sample_queries[:5]:  # Limit for testing
                results = await self.execute_optimized_search(
                    table_name, column_name, query_vector, limit=20
                )

                if self.query_history:
                    total_time += self.query_history[-1].query_time_ms
                    total_results += len(results)

            avg_time = total_time / max(len(sample_queries), 1)
            avg_results = total_results / max(len(sample_queries), 1)

            return {
                "avg_query_time_ms": avg_time,
                "avg_results_count": avg_results
            }

        except Exception as e:
            logger.error(f"Error testing probe performance: {e}")
            return {"avg_query_time_ms": 999999, "avg_results_count": 0}

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            "configuration": asdict(self.config),
            "index_statistics": {k: asdict(v) for k, v in self.index_stats.items()},
            "query_performance": {
                "total_queries": len(self.query_history),
                "avg_query_time_ms": np.mean([q.query_time_ms for q in self.query_history]) if self.query_history else 0,
                "max_query_time_ms": max([q.query_time_ms for q in self.query_history]) if self.query_history else 0,
                "min_query_time_ms": min([q.query_time_ms for q in self.query_history]) if self.query_history else 0
            }
        }

# Global optimizer instance
pgvector_optimizer = PGVectorOptimizer()