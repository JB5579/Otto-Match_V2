"""
Query Optimizer and Performance Monitor for Otto.AI
Implements Story 1-8: Query optimization and performance monitoring

Features:
- Real-time query performance monitoring
- Automatic query optimization suggestions
- Performance metrics collection and analysis
- Slow query detection and alerting
- Query pattern analysis and optimization
"""

import asyncio
import time
import logging
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
import psutil
import threading

logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    """Metrics for a single query execution"""
    query_id: str
    query_text: str
    execution_time_ms: float
    cpu_usage_percent: float
    memory_usage_mb: float
    rows_examined: int
    rows_returned: int
    index_used: bool
    cache_hit: bool
    similarity_scores: List[float] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    query_type: str = "unknown"
    optimization_hints: List[str] = field(default_factory=list)

@dataclass
class QueryPattern:
    """Pattern for recurring queries"""
    pattern_hash: str
    query_template: str
    frequency: int
    avg_execution_time_ms: float
    min_execution_time_ms: float
    max_execution_time_ms: float
    total_executions: int
    last_seen: datetime
    optimization_applied: bool = False
    optimization_results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceThresholds:
    """Performance thresholds for alerting"""
    slow_query_threshold_ms: float = 1000.0  # 1 second
    critical_query_threshold_ms: float = 5000.0  # 5 seconds
    high_cpu_threshold_percent: float = 80.0
    high_memory_threshold_mb: float = 1000.0
    low_cache_hit_rate_percent: float = 50.0
    low_similarity_threshold: float = 0.5

class QueryOptimizer:
    """Query optimization and performance monitoring service"""

    def __init__(self, max_history_size: int = 10000, pattern_window_minutes: int = 60):
        self.max_history_size = max_history_size
        self.pattern_window_minutes = pattern_window_minutes

        # Query history and patterns
        self.query_history: deque[QueryMetrics] = deque(maxlen=max_history_size)
        self.query_patterns: Dict[str, QueryPattern] = {}
        self.slow_queries: List[QueryMetrics] = []

        # Performance thresholds
        self.thresholds = PerformanceThresholds()

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread: Optional[threading.Thread] = None

        # Optimization callbacks
        self.optimization_callbacks: List[Callable] = []

        # System metrics
        self.system_metrics = {
            "cpu_usage": deque(maxlen=100),
            "memory_usage": deque(maxlen=100),
            "query_rate": deque(maxlen=100)
        }

    async def start_monitoring(self) -> bool:
        """Start performance monitoring"""
        try:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitor_system_metrics, daemon=True)
            self.monitoring_thread.start()

            logger.info("✅ Query optimizer monitoring started")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start monitoring: {e}")
            return False

    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("⏹️ Query optimizer monitoring stopped")

    async def record_query(
        self,
        query_text: str,
        execution_time_ms: float,
        rows_examined: int = 0,
        rows_returned: int = 0,
        index_used: bool = False,
        cache_hit: bool = False,
        similarity_scores: Optional[List[float]] = None,
        query_type: str = "unknown"
    ) -> QueryMetrics:
        """Record query execution metrics"""
        try:
            # Get system metrics at query time
            cpu_usage = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            memory_usage_mb = memory_info.used / (1024 * 1024)

            # Create query metrics
            metrics = QueryMetrics(
                query_id=self._generate_query_id(query_text),
                query_text=query_text,
                execution_time_ms=execution_time_ms,
                cpu_usage_percent=cpu_usage,
                memory_usage_mb=memory_usage_mb,
                rows_examined=rows_examined,
                rows_returned=rows_returned,
                index_used=index_used,
                cache_hit=cache_hit,
                similarity_scores=similarity_scores or [],
                query_type=query_type,
                optimization_hints=[]
            )

            # Add to history
            self.query_history.append(metrics)

            # Detect slow queries
            if execution_time_ms > self.thresholds.slow_query_threshold_ms:
                self.slow_queries.append(metrics)
                await self._handle_slow_query(metrics)

            # Update query patterns
            await self._update_query_patterns(metrics)

            # Generate optimization hints
            await self._generate_optimization_hints(metrics)

            logger.debug(f"Recorded query: {metrics.query_id[:8]} in {execution_time_ms:.2f}ms")
            return metrics

        except Exception as e:
            logger.error(f"❌ Failed to record query metrics: {e}")
            return None

    async def optimize_query(self, query_text: str, query_type: str = "select") -> Dict[str, Any]:
        """Analyze and optimize a query"""
        try:
            optimization_result = {
                "original_query": query_text,
                "optimizations": [],
                "estimated_improvement_percent": 0,
                "optimized_query": query_text,
                "reasoning": []
            }

            # Pattern-based optimizations
            pattern = self._extract_query_pattern(query_text)
            if pattern in self.query_patterns:
                query_pattern = self.query_patterns[pattern]
                if query_pattern.optimization_applied:
                    optimization_result["optimizations"].append("Pattern-based optimization already applied")

            # Similarity search optimizations
            if "similarity" in query_text.lower() or "<=>" in query_text:
                similarity_optimizations = await self._optimize_similarity_query(query_text)
                optimization_result["optimizations"].extend(similarity_optimizations)

            # Index usage optimization
            if not self._query_uses_index(query_text):
                index_hints = await self._suggest_index_usage(query_text)
                optimization_result["optimizations"].extend(index_hints)

            # Pagination optimization
            if "LIMIT" in query_text.upper() and "OFFSET" in query_text.upper():
                pagination_opt = await self._optimize_pagination(query_text)
                optimization_result["optimizations"].extend(pagination_opt)

            # JOIN optimization
            if "JOIN" in query_text.upper():
                join_opt = await self._optimize_joins(query_text)
                optimization_result["optimizations"].extend(join_opt)

            # Apply simple optimizations
            optimized_query = self._apply_simple_optimizations(query_text)
            if optimized_query != query_text:
                optimization_result["optimized_query"] = optimized_query
                optimization_result["estimated_improvement_percent"] = 10  # Conservative estimate

            # Call custom optimization callbacks
            for callback in self.optimization_callbacks:
                try:
                    custom_result = await callback(query_text, query_type)
                    if custom_result:
                        optimization_result["optimizations"].extend(
                            custom_result.get("optimizations", [])
                        )
                except Exception as e:
                    logger.warning(f"Custom optimization callback failed: {e}")

            return optimization_result

        except Exception as e:
            logger.error(f"❌ Failed to optimize query: {e}")
            return {"error": str(e), "original_query": query_text}

    async def get_performance_report(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            recent_queries = [
                q for q in self.query_history
                if q.timestamp > cutoff_time
            ]

            if not recent_queries:
                return {"message": "No queries in specified time window"}

            # Calculate statistics
            execution_times = [q.execution_time_ms for q in recent_queries]
            cpu_usage = [q.cpu_usage_percent for q in recent_queries]
            memory_usage = [q.memory_usage_mb for q in recent_queries]

            report = {
                "time_window_minutes": time_window_minutes,
                "total_queries": len(recent_queries),
                "query_rate_per_minute": len(recent_queries) / time_window_minutes,
                "performance_metrics": {
                    "avg_execution_time_ms": np.mean(execution_times),
                    "median_execution_time_ms": np.median(execution_times),
                    "p95_execution_time_ms": np.percentile(execution_times, 95),
                    "max_execution_time_ms": np.max(execution_times),
                    "min_execution_time_ms": np.min(execution_times)
                },
                "resource_usage": {
                    "avg_cpu_usage_percent": np.mean(cpu_usage),
                    "max_cpu_usage_percent": np.max(cpu_usage),
                    "avg_memory_usage_mb": np.mean(memory_usage),
                    "max_memory_usage_mb": np.max(memory_usage)
                },
                "query_analysis": {
                    "slow_queries": len([q for q in recent_queries if q.execution_time_ms > self.thresholds.slow_query_threshold_ms]),
                    "critical_queries": len([q for q in recent_queries if q.execution_time_ms > self.thresholds.critical_query_threshold_ms]),
                    "index_usage_rate": len([q for q in recent_queries if q.index_used]) / len(recent_queries) * 100,
                    "cache_hit_rate": len([q for q in recent_queries if q.cache_hit]) / len(recent_queries) * 100,
                    "similarity_queries": len([q for q in recent_queries if "<=>" in q.query_text])
                },
                "query_types": self._analyze_query_types(recent_queries),
                "top_slow_queries": self._get_top_slow_queries(recent_queries, 5),
                "recommendations": await self._generate_recommendations(recent_queries)
            }

            return report

        except Exception as e:
            logger.error(f"❌ Failed to generate performance report: {e}")
            return {"error": str(e)}

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics"""
        try:
            # Get recent queries (last 5 minutes)
            cutoff_time = datetime.now() - timedelta(minutes=5)
            recent_queries = [
                q for q in self.query_history
                if q.timestamp > cutoff_time
            ]

            # Calculate current metrics
            if recent_queries:
                avg_execution_time = np.mean([q.execution_time_ms for q in recent_queries])
                current_qps = len(recent_queries) / 300  # Queries per second over 5 minutes
                slow_query_rate = len([q for q in recent_queries if q.execution_time_ms > self.thresholds.slow_query_threshold_ms]) / len(recent_queries) * 100
            else:
                avg_execution_time = 0
                current_qps = 0
                slow_query_rate = 0

            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()

            metrics = {
                "timestamp": datetime.now().isoformat(),
                "query_performance": {
                    "avg_execution_time_ms": avg_execution_time,
                    "queries_per_second": current_qps,
                    "slow_query_rate_percent": slow_query_rate,
                    "active_queries": len(recent_queries)
                },
                "system_resources": {
                    "cpu_usage_percent": cpu_percent,
                    "memory_usage_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3)
                },
                "cache_performance": {
                    "hit_rate_percent": len([q for q in recent_queries if q.cache_hit]) / max(len(recent_queries), 1) * 100,
                    "total_cache_hits": len([q for q in recent_queries if q.cache_hit])
                },
                "alerts": await self._check_alert_conditions(recent_queries)
            }

            return metrics

        except Exception as e:
            logger.error(f"❌ Failed to get real-time metrics: {e}")
            return {"error": str(e)}

    async def apply_index_hints(self, query_text: str, index_hints: List[str]) -> str:
        """Apply index hints to query"""
        try:
            # Simple index hint application (PostgreSQL doesn't support hints directly)
            # This would typically involve query rewriting or configuration

            optimized_query = query_text

            # For now, just document the recommended indexes
            if index_hints:
                logger.info(f"Recommended indexes for query: {index_hints}")

            return optimized_query

        except Exception as e:
            logger.error(f"❌ Failed to apply index hints: {e}")
            return query_text

    def add_optimization_callback(self, callback: Callable):
        """Add custom optimization callback"""
        self.optimization_callbacks.append(callback)

    def _generate_query_id(self, query_text: str) -> str:
        """Generate unique ID for query"""
        return hashlib.md5(f"{query_text}{time.time()}".encode()).hexdigest()[:16]

    def _extract_query_pattern(self, query_text: str) -> str:
        """Extract normalized query pattern"""
        # Simple normalization - remove specific values
        import re

        # Remove numeric values
        normalized = re.sub(r'\b\d+\b', '?', query_text)

        # Remove quoted strings
        normalized = re.sub(r"'[^']*'", "'?'", normalized)
        normalized = re.sub(r'"[^"]*"', '"?"', normalized)

        # Normalize whitespace
        normalized = ' '.join(normalized.split())

        return hashlib.md5(normalized.encode()).hexdigest()

    async def _update_query_patterns(self, metrics: QueryMetrics):
        """Update query pattern statistics"""
        pattern = self._extract_query_pattern(metrics.query_text)

        if pattern not in self.query_patterns:
            self.query_patterns[pattern] = QueryPattern(
                pattern_hash=pattern,
                query_template=metrics.query_text[:100] + "...",
                frequency=1,
                avg_execution_time_ms=metrics.execution_time_ms,
                min_execution_time_ms=metrics.execution_time_ms,
                max_execution_time_ms=metrics.execution_time_ms,
                total_executions=1,
                last_seen=metrics.timestamp
            )
        else:
            pattern_stats = self.query_patterns[pattern]
            pattern_stats.frequency += 1
            pattern_stats.total_executions += 1
            pattern_stats.last_seen = metrics.timestamp

            # Update execution time statistics
            total_time = pattern_stats.avg_execution_time_ms * (pattern_stats.total_executions - 1) + metrics.execution_time_ms
            pattern_stats.avg_execution_time_ms = total_time / pattern_stats.total_executions
            pattern_stats.min_execution_time_ms = min(pattern_stats.min_execution_time_ms, metrics.execution_time_ms)
            pattern_stats.max_execution_time_ms = max(pattern_stats.max_execution_time_ms, metrics.execution_time_ms)

    async def _generate_optimization_hints(self, metrics: QueryMetrics):
        """Generate optimization hints for a query"""
        hints = []

        # Performance-based hints
        if metrics.execution_time_ms > self.thresholds.slow_query_threshold_ms:
            hints.append("Consider adding indexes or optimizing query structure")

        if metrics.rows_examined > metrics.rows_returned * 10:
            hints.append("Query examines many more rows than returned - consider better filtering")

        if not metrics.index_used and metrics.execution_time_ms > 100:
            hints.append("No index used - consider adding appropriate indexes")

        if metrics.cache_hit == False and metrics.query_type in ["select", "similarity_search"]:
            hints.append("Consider caching frequent query results")

        # Similarity search specific hints
        if metrics.similarity_scores:
            avg_similarity = np.mean(metrics.similarity_scores)
            if avg_similarity < self.thresholds.low_similarity_threshold:
                hints.append(f"Low average similarity ({avg_similarity:.2f}) - consider adjusting similarity threshold")

        metrics.optimization_hints = hints

    async def _handle_slow_query(self, metrics: QueryMetrics):
        """Handle slow query detection"""
        logger.warning(f"🐌 Slow query detected: {metrics.query_id[:8]} took {metrics.execution_time_ms:.2f}ms")

        # Could trigger alerts, logging, or automatic optimizations here
        if metrics.execution_time_ms > self.thresholds.critical_query_threshold_ms:
            logger.error(f"🚨 CRITICAL: Query {metrics.query_id[:8]} took {metrics.execution_time_ms:.2f}ms")

    async def _optimize_similarity_query(self, query_text: str) -> List[str]:
        """Optimize similarity search queries"""
        optimizations = []

        # Check for proper index usage
        if "<=>" in query_text:
            optimizations.append("Ensure vector index exists for similarity search")
            optimizations.append("Consider setting appropriate ivfflat.probes or hnsw.ef_search")

        # Check for limit clause
        if "LIMIT" not in query_text.upper():
            optimizations.append("Add LIMIT clause to similarity searches")

        return optimizations

    async def _suggest_index_usage(self, query_text: str) -> List[str]:
        """Suggest indexes for query"""
        suggestions = []

        # Simple heuristic - look for WHERE clause columns
        if "WHERE" in query_text.upper():
            suggestions.append("Consider indexes on WHERE clause columns")

        if "ORDER BY" in query_text.upper():
            suggestions.append("Consider indexes on ORDER BY columns")

        return suggestions

    async def _optimize_pagination(self, query_text: str) -> List[str]:
        """Optimize pagination queries"""
        optimizations = []

        # Suggest keyset pagination for large offsets
        if "OFFSET" in query_text.upper():
            optimizations.append("Consider keyset pagination for large offsets")

        return optimizations

    async def _optimize_joins(self, query_text: str) -> List[str]:
        """Optimize JOIN queries"""
        optimizations = []

        # Basic join optimization suggestions
        optimizations.append("Ensure join columns are indexed")
        optimizations.append("Consider JOIN order based on table sizes")

        return optimizations

    def _apply_simple_optimizations(self, query_text: str) -> str:
        """Apply simple query optimizations"""
        optimized = query_text

        # Remove redundant whitespace
        optimized = ' '.join(optimized.split())

        # Add explicit LIMIT if missing (conservative)
        if "SELECT" in optimized.upper() and "LIMIT" not in optimized.upper():
            optimized += " LIMIT 1000"

        return optimized

    def _query_uses_index(self, query_text: str) -> bool:
        """Check if query likely uses an index"""
        # Simple heuristic - this would be more sophisticated with EXPLAIN
        if "WHERE" in query_text.upper():
            return True
        if "<=>" in query_text:  # Vector similarity
            return True
        return False

    def _analyze_query_types(self, queries: List[QueryMetrics]) -> Dict[str, int]:
        """Analyze distribution of query types"""
        type_counts = defaultdict(int)
        for query in queries:
            type_counts[query.query_type] += 1
        return dict(type_counts)

    def _get_top_slow_queries(self, queries: List[QueryMetrics], limit: int) -> List[Dict[str, Any]]:
        """Get top slowest queries"""
        sorted_queries = sorted(queries, key=lambda q: q.execution_time_ms, reverse=True)[:limit]

        return [
            {
                "query_id": q.query_id[:8],
                "execution_time_ms": q.execution_time_ms,
                "query_type": q.query_type,
                "rows_returned": q.rows_returned,
                "timestamp": q.timestamp.isoformat()
            }
            for q in sorted_queries
        ]

    async def _generate_recommendations(self, queries: List[QueryMetrics]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        if not queries:
            return recommendations

        # Analyze execution times
        avg_time = np.mean([q.execution_time_ms for q in queries])
        if avg_time > 500:
            recommendations.append("Average query time is high - consider query optimization")

        # Analyze index usage
        index_rate = len([q for q in queries if q.index_used]) / len(queries) * 100
        if index_rate < 50:
            recommendations.append("Low index usage rate - ensure proper indexes exist")

        # Analyze cache hit rate
        cache_rate = len([q for q in queries if q.cache_hit]) / len(queries) * 100
        if cache_rate < self.thresholds.low_cache_hit_rate_percent:
            recommendations.append("Low cache hit rate - consider caching frequent queries")

        return recommendations

    async def _check_alert_conditions(self, recent_queries: List[QueryMetrics]) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []

        # Check system resources
        cpu_percent = psutil.cpu_percent()
        if cpu_percent > self.thresholds.high_cpu_threshold_percent:
            alerts.append({
                "type": "high_cpu",
                "severity": "warning",
                "message": f"High CPU usage: {cpu_percent:.1f}%",
                "timestamp": datetime.now().isoformat()
            })

        memory = psutil.virtual_memory()
        if memory.used / (1024 * 1024) > self.thresholds.high_memory_threshold_mb:
            alerts.append({
                "type": "high_memory",
                "severity": "warning",
                "message": f"High memory usage: {memory.used / (1024 * 1024):.1f} MB",
                "timestamp": datetime.now().isoformat()
            })

        # Check query performance
        if recent_queries:
            critical_queries = [
                q for q in recent_queries
                if q.execution_time_ms > self.thresholds.critical_query_threshold_ms
            ]
            if critical_queries:
                alerts.append({
                    "type": "critical_queries",
                    "severity": "error",
                    "message": f"{len(critical_queries)} critical slow queries detected",
                    "timestamp": datetime.now().isoformat()
                })

        return alerts

    def _monitor_system_metrics(self):
        """Monitor system metrics in background thread"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                cpu_usage = psutil.cpu_percent()
                memory = psutil.virtual_memory()

                self.system_metrics["cpu_usage"].append(cpu_usage)
                self.system_metrics["memory_usage"].append(memory.percent)

                # Calculate query rate
                recent_time = datetime.now() - timedelta(seconds=10)
                recent_count = len([
                    q for q in self.query_history
                    if q.timestamp > recent_time
                ])
                query_rate = recent_count / 10
                self.system_metrics["query_rate"].append(query_rate)

                time.sleep(1)

            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                time.sleep(5)

# Global optimizer instance
query_optimizer = QueryOptimizer()