"""Metrics and tracing for observability."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import structlog

logger = structlog.get_logger()


class MetricType(str, Enum):
    """Metric type enumeration."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """Metric value with timestamp."""

    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class MetricStats:
    """Metric statistics."""

    count: int = 0
    total: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")
    avg: float = 0.0
    
    def update(self, value: float) -> None:
        """Update statistics with new value."""
        self.count += 1
        self.total += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.avg = self.total / self.count


class MetricsCollector:
    """Metrics collector for system observability."""

    def __init__(
        self, 
        enabled: bool = True,
        collect_query_metrics: bool = True,
        collect_sql_metrics: bool = True,
        collect_db_metrics: bool = True,
    ):
        """
        Initialize metrics collector.

        Args:
            enabled: Whether metrics collection is enabled
            collect_query_metrics: Collect query-level metrics
            collect_sql_metrics: Collect SQL generation/execution metrics
            collect_db_metrics: Collect database connection metrics
        """
        self.enabled = enabled
        self.collect_query = collect_query_metrics
        self.collect_sql = collect_sql_metrics
        self.collect_db = collect_db_metrics
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[MetricValue]] = defaultdict(list)
        self._timers: dict[str, MetricStats] = defaultdict(MetricStats)
    
    def _should_collect(self, metric: str) -> bool:
        """Check if metric should be collected based on configuration."""
        if not self.enabled:
            return False
        
        # Check metric category
        if metric.startswith("mcp.query.") and not self.collect_query:
            return False
        if (metric.startswith("mcp.sql.") and not self.collect_sql):
            return False
        if (metric.startswith("mcp.db.") or 
            metric.startswith("mcp.schema.") or
            metric.startswith("mcp.validation.")) and not self.collect_db:
            return False
        
        return True

    def increment(self, metric: str, value: float = 1.0, labels: Optional[dict[str, str]] = None) -> None:
        """
        Increment a counter metric.

        Args:
            metric: Metric name
            value: Increment value
            labels: Optional labels
        """
        if not self._should_collect(metric):
            return

        key = self._make_key(metric, labels)
        self._counters[key] += value

        logger.debug("Counter incremented", metric=metric, value=value, labels=labels)

    def set_gauge(self, metric: str, value: float, labels: Optional[dict[str, str]] = None) -> None:
        """
        Set a gauge metric.

        Args:
            metric: Metric name
            value: Gauge value
            labels: Optional labels
        """
        if not self._should_collect(metric):
            return

        key = self._make_key(metric, labels)
        self._gauges[key] = value

        logger.debug("Gauge set", metric=metric, value=value, labels=labels)

    def record_histogram(self, metric: str, value: float, labels: Optional[dict[str, str]] = None) -> None:
        """
        Record a histogram value.

        Args:
            metric: Metric name
            value: Value to record
            labels: Optional labels
        """
        if not self._should_collect(metric):
            return

        key = self._make_key(metric, labels)
        self._histograms[key].append(MetricValue(value=value, labels=labels or {}))

        # Keep only recent values (last 1000)
        if len(self._histograms[key]) > 1000:
            self._histograms[key] = self._histograms[key][-1000:]

        logger.debug("Histogram recorded", metric=metric, value=value, labels=labels)

    def record_timer(self, metric: str, duration_ms: float, labels: Optional[dict[str, str]] = None) -> None:
        """
        Record a timer metric.

        Args:
            metric: Metric name
            duration_ms: Duration in milliseconds
            labels: Optional labels
        """
        if not self._should_collect(metric):
            return

        key = self._make_key(metric, labels)
        self._timers[key].update(duration_ms)

        logger.debug("Timer recorded", metric=metric, duration_ms=duration_ms, labels=labels)

    def get_counter(self, metric: str, labels: Optional[dict[str, str]] = None) -> float:
        """Get counter value."""
        key = self._make_key(metric, labels)
        return self._counters.get(key, 0.0)

    def get_gauge(self, metric: str, labels: Optional[dict[str, str]] = None) -> Optional[float]:
        """Get gauge value."""
        key = self._make_key(metric, labels)
        return self._gauges.get(key)

    def get_histogram_stats(self, metric: str, labels: Optional[dict[str, str]] = None) -> Optional[dict[str, Any]]:
        """Get histogram statistics."""
        key = self._make_key(metric, labels)
        values = self._histograms.get(key, [])

        if not values:
            return None

        value_list = [v.value for v in values]
        return {
            "count": len(value_list),
            "min": min(value_list),
            "max": max(value_list),
            "avg": sum(value_list) / len(value_list),
            "p50": self._percentile(value_list, 50),
            "p95": self._percentile(value_list, 95),
            "p99": self._percentile(value_list, 99),
        }

    def get_timer_stats(self, metric: str, labels: Optional[dict[str, str]] = None) -> Optional[dict[str, Any]]:
        """Get timer statistics."""
        key = self._make_key(metric, labels)
        stats = self._timers.get(key)

        if not stats or stats.count == 0:
            return None

        return {
            "count": stats.count,
            "total_ms": stats.total,
            "min_ms": stats.min,
            "max_ms": stats.max,
            "avg_ms": stats.avg,
        }

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                key: self.get_histogram_stats(key) 
                for key in self._histograms.keys()
            },
            "timers": {
                key: self.get_timer_stats(key)
                for key in self._timers.keys()
            },
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._timers.clear()
        logger.info("All metrics reset")

    def _make_key(self, metric: str, labels: Optional[dict[str, str]]) -> str:
        """Make metric key from name and labels."""
        if not labels:
            return metric
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{metric}{{{label_str}}}"

    @staticmethod
    def _percentile(values: list[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]


class MetricsTimer:
    """Context manager for timing operations."""

    def __init__(self, metrics: MetricsCollector, metric_name: str, labels: Optional[dict[str, str]] = None):
        """
        Initialize timer.

        Args:
            metrics: Metrics collector
            metric_name: Metric name
            labels: Optional labels
        """
        self.metrics = metrics
        self.metric_name = metric_name
        self.labels = labels
        self.start_time: Optional[float] = None

    def __enter__(self) -> "MetricsTimer":
        """Start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timer and record metric."""
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            self.metrics.record_timer(self.metric_name, duration_ms, self.labels)


# Standard metric names
class StandardMetrics:
    """Standard metric names."""

    # Query metrics
    QUERY_TOTAL = "mcp.query.total"
    QUERY_SUCCESS = "mcp.query.success"
    QUERY_ERROR = "mcp.query.error"
    QUERY_DURATION = "mcp.query.duration_ms"

    # SQL generation metrics
    SQL_GENERATION_TOTAL = "mcp.sql.generation.total"
    SQL_GENERATION_SUCCESS = "mcp.sql.generation.success"
    SQL_GENERATION_ERROR = "mcp.sql.generation.error"
    SQL_GENERATION_DURATION = "mcp.sql.generation.duration_ms"

    # SQL execution metrics
    SQL_EXECUTION_TOTAL = "mcp.sql.execution.total"
    SQL_EXECUTION_SUCCESS = "mcp.sql.execution.success"
    SQL_EXECUTION_ERROR = "mcp.sql.execution.error"
    SQL_EXECUTION_DURATION = "mcp.sql.execution.duration_ms"
    SQL_EXECUTION_ROWS = "mcp.sql.execution.rows"

    # Validation metrics
    VALIDATION_TOTAL = "mcp.validation.total"
    VALIDATION_SUCCESS = "mcp.validation.success"
    VALIDATION_FAILED = "mcp.validation.failed"
    VALIDATION_DURATION = "mcp.validation.duration_ms"

    # Rate limit metrics
    RATE_LIMIT_CHECKS = "mcp.rate_limit.checks"
    RATE_LIMIT_EXCEEDED = "mcp.rate_limit.exceeded"

    # Database metrics
    DB_CONNECTION_POOL_SIZE = "mcp.db.connection_pool.size"
    DB_CONNECTION_POOL_AVAILABLE = "mcp.db.connection_pool.available"

    # Schema cache metrics
    SCHEMA_CACHE_LOADED = "mcp.schema.cache.loaded"
    SCHEMA_CACHE_TABLES = "mcp.schema.cache.tables"
