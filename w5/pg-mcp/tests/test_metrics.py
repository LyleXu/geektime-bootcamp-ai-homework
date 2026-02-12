"""Tests for metrics collector."""

import time

import pytest

from pg_mcp_server.utils.metrics import (
    MetricType,
    MetricsCollector,
    MetricsTimer,
    StandardMetrics,
)


class TestMetricsCollector:
    """Test metrics collector."""

    def test_initialization(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector(enabled=True)
        assert collector.enabled is True
        
        collector_disabled = MetricsCollector(enabled=False)
        assert collector_disabled.enabled is False

    def test_increment_counter(self):
        """Test incrementing counters."""
        collector = MetricsCollector(enabled=True)
        
        # Increment without labels
        collector.increment("test.counter")
        assert collector.get_counter("test.counter") == 1.0
        
        # Increment again
        collector.increment("test.counter", value=2.5)
        assert collector.get_counter("test.counter") == 3.5
        
        # Increment with labels
        collector.increment("test.counter", labels={"db": "test1"})
        collector.increment("test.counter", labels={"db": "test1"})
        assert collector.get_counter("test.counter", labels={"db": "test1"}) == 2.0

    def test_set_gauge(self):
        """Test setting gauge values."""
        collector = MetricsCollector(enabled=True)
        
        # Set gauge
        collector.set_gauge("test.gauge", 42.5)
        assert collector.get_gauge("test.gauge") == 42.5
        
        # Update gauge
        collector.set_gauge("test.gauge", 100.0)
        assert collector.get_gauge("test.gauge") == 100.0
        
        # Set with labels
        collector.set_gauge("test.gauge", 50.0, labels={"db": "test1"})
        assert collector.get_gauge("test.gauge", labels={"db": "test1"}) == 50.0

    def test_record_histogram(self):
        """Test recording histogram values."""
        collector = MetricsCollector(enabled=True)
        
        # Record values
        for i in range(10):
            collector.record_histogram("test.histogram", float(i * 10))
        
        # Get stats
        stats = collector.get_histogram_stats("test.histogram")
        assert stats is not None
        assert stats["count"] == 10
        assert stats["min"] == 0.0
        assert stats["max"] == 90.0
        assert stats["avg"] == 45.0

    def test_histogram_percentiles(self):
        """Test histogram percentile calculations."""
        collector = MetricsCollector(enabled=True)
        
        # Record 100 values (0-99)
        for i in range(100):
            collector.record_histogram("test.histogram", float(i))
        
        stats = collector.get_histogram_stats("test.histogram")
        assert stats is not None
        assert stats["p50"] == pytest.approx(49.0, abs=2.0)
        assert stats["p95"] == pytest.approx(94.0, abs=2.0)
        assert stats["p99"] == pytest.approx(98.0, abs=2.0)

    def test_record_timer(self):
        """Test recording timer metrics."""
        collector = MetricsCollector(enabled=True)
        
        # Record durations
        collector.record_timer("test.timer", 100.5)
        collector.record_timer("test.timer", 200.5)
        collector.record_timer("test.timer", 150.5)
        
        # Get stats
        stats = collector.get_timer_stats("test.timer")
        assert stats is not None
        assert stats["count"] == 3
        assert stats["total_ms"] == pytest.approx(451.5, abs=0.1)
        assert stats["min_ms"] == 100.5
        assert stats["max_ms"] == 200.5
        assert stats["avg_ms"] == pytest.approx(150.5, abs=0.1)

    def test_metrics_with_labels(self):
        """Test metrics with different labels are tracked separately."""
        collector = MetricsCollector(enabled=True)
        
        # Record with different labels
        collector.increment("requests", labels={"db": "db1"})
        collector.increment("requests", labels={"db": "db1"})
        collector.increment("requests", labels={"db": "db2"})
        
        # Check separate counters
        assert collector.get_counter("requests", labels={"db": "db1"}) == 2.0
        assert collector.get_counter("requests", labels={"db": "db2"}) == 1.0

    def test_get_all_metrics(self):
        """Test getting all metrics."""
        collector = MetricsCollector(enabled=True)
        
        # Add various metrics
        collector.increment("counter1")
        collector.set_gauge("gauge1", 42.0)
        collector.record_histogram("hist1", 100.0)
        collector.record_timer("timer1", 50.5)
        
        # Get all metrics
        all_metrics = collector.get_all_metrics()
        
        assert "counters" in all_metrics
        assert "gauges" in all_metrics
        assert "histograms" in all_metrics
        assert "timers" in all_metrics
        
        assert all_metrics["counters"]["counter1"] == 1.0
        assert all_metrics["gauges"]["gauge1"] == 42.0

    def test_reset_metrics(self):
        """Test resetting all metrics."""
        collector = MetricsCollector(enabled=True)
        
        # Add metrics
        collector.increment("counter1")
        collector.set_gauge("gauge1", 42.0)
        collector.record_histogram("hist1", 100.0)
        collector.record_timer("timer1", 50.5)
        
        # Verify metrics exist
        assert collector.get_counter("counter1") == 1.0
        assert collector.get_gauge("gauge1") == 42.0
        
        # Reset
        collector.reset()
        
        # Verify metrics are cleared
        assert collector.get_counter("counter1") == 0.0
        assert collector.get_gauge("gauge1") is None
        assert collector.get_histogram_stats("hist1") is None
        assert collector.get_timer_stats("timer1") is None

    def test_disabled_collector(self):
        """Test that disabled collector doesn't record metrics."""
        collector = MetricsCollector(enabled=False)
        
        # Try to record metrics
        collector.increment("counter1")
        collector.set_gauge("gauge1", 42.0)
        collector.record_histogram("hist1", 100.0)
        collector.record_timer("timer1", 50.5)
        
        # Verify nothing was recorded
        all_metrics = collector.get_all_metrics()
        assert len(all_metrics["counters"]) == 0
        assert len(all_metrics["gauges"]) == 0
        assert len(all_metrics["histograms"]) == 0
        assert len(all_metrics["timers"]) == 0

    def test_histogram_size_limit(self):
        """Test that histogram maintains size limit."""
        collector = MetricsCollector(enabled=True)
        
        # Record more than 1000 values
        for i in range(1500):
            collector.record_histogram("test.histogram", float(i))
        
        stats = collector.get_histogram_stats("test.histogram")
        assert stats is not None
        # Should keep only last 1000
        assert stats["count"] == 1000

    def test_empty_histogram_stats(self):
        """Test getting stats for empty histogram."""
        collector = MetricsCollector(enabled=True)
        
        stats = collector.get_histogram_stats("nonexistent")
        assert stats is None

    def test_empty_timer_stats(self):
        """Test getting stats for empty timer."""
        collector = MetricsCollector(enabled=True)
        
        stats = collector.get_timer_stats("nonexistent")
        assert stats is None


class TestMetricsTimer:
    """Test metrics timer context manager."""

    def test_timer_context_manager(self):
        """Test using timer as context manager."""
        collector = MetricsCollector(enabled=True)
        
        with MetricsTimer(collector, "test.operation"):
            time.sleep(0.01)  # Simulate work
        
        # Check timer was recorded
        stats = collector.get_timer_stats("test.operation")
        assert stats is not None
        assert stats["count"] == 1
        assert stats["min_ms"] >= 10.0  # At least 10ms

    def test_timer_with_labels(self):
        """Test timer with labels."""
        collector = MetricsCollector(enabled=True)
        
        with MetricsTimer(collector, "test.operation", labels={"db": "test1"}):
            time.sleep(0.01)
        
        # Check labeled timer
        stats = collector.get_timer_stats("test.operation", labels={"db": "test1"})
        assert stats is not None
        assert stats["count"] == 1

    def test_timer_with_exception(self):
        """Test that timer still records even if exception occurs."""
        collector = MetricsCollector(enabled=True)
        
        try:
            with MetricsTimer(collector, "test.operation"):
                time.sleep(0.01)
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Timer should still be recorded
        stats = collector.get_timer_stats("test.operation")
        assert stats is not None
        assert stats["count"] == 1

    def test_multiple_timer_calls(self):
        """Test multiple timer calls."""
        collector = MetricsCollector(enabled=True)
        
        # Record multiple times
        for _ in range(5):
            with MetricsTimer(collector, "test.operation"):
                time.sleep(0.005)
        
        stats = collector.get_timer_stats("test.operation")
        assert stats is not None
        assert stats["count"] == 5

    def test_timer_disabled_collector(self):
        """Test timer with disabled collector."""
        collector = MetricsCollector(enabled=False)
        
        with MetricsTimer(collector, "test.operation"):
            time.sleep(0.01)
        
        # Nothing should be recorded
        stats = collector.get_timer_stats("test.operation")
        assert stats is None


class TestStandardMetrics:
    """Test standard metric names."""

    def test_standard_metric_names(self):
        """Test that standard metric names are defined."""
        # Query metrics
        assert hasattr(StandardMetrics, "QUERY_TOTAL")
        assert hasattr(StandardMetrics, "QUERY_SUCCESS")
        assert hasattr(StandardMetrics, "QUERY_ERROR")
        assert hasattr(StandardMetrics, "QUERY_DURATION")
        
        # SQL generation metrics
        assert hasattr(StandardMetrics, "SQL_GENERATION_TOTAL")
        assert hasattr(StandardMetrics, "SQL_GENERATION_SUCCESS")
        assert hasattr(StandardMetrics, "SQL_GENERATION_ERROR")
        assert hasattr(StandardMetrics, "SQL_GENERATION_DURATION")
        
        # SQL execution metrics
        assert hasattr(StandardMetrics, "SQL_EXECUTION_TOTAL")
        assert hasattr(StandardMetrics, "SQL_EXECUTION_SUCCESS")
        assert hasattr(StandardMetrics, "SQL_EXECUTION_ERROR")
        assert hasattr(StandardMetrics, "SQL_EXECUTION_DURATION")
        assert hasattr(StandardMetrics, "SQL_EXECUTION_ROWS")
        
        # Validation metrics
        assert hasattr(StandardMetrics, "VALIDATION_TOTAL")
        assert hasattr(StandardMetrics, "VALIDATION_SUCCESS")
        assert hasattr(StandardMetrics, "VALIDATION_FAILED")
        assert hasattr(StandardMetrics, "VALIDATION_DURATION")
        
        # Rate limit metrics
        assert hasattr(StandardMetrics, "RATE_LIMIT_CHECKS")
        assert hasattr(StandardMetrics, "RATE_LIMIT_EXCEEDED")
        
        # Schema cache metrics
        assert hasattr(StandardMetrics, "SCHEMA_CACHE_LOADED")
        assert hasattr(StandardMetrics, "SCHEMA_CACHE_TABLES")

    def test_metric_name_format(self):
        """Test that metric names follow convention."""
        # All metrics should start with "mcp."
        assert StandardMetrics.QUERY_TOTAL.startswith("mcp.")
        assert StandardMetrics.SQL_GENERATION_TOTAL.startswith("mcp.")
        assert StandardMetrics.RATE_LIMIT_CHECKS.startswith("mcp.")

    def test_using_standard_metrics(self):
        """Test using standard metrics with collector."""
        collector = MetricsCollector(enabled=True)
        
        # Use standard metric names
        collector.increment(StandardMetrics.QUERY_TOTAL)
        collector.increment(StandardMetrics.QUERY_SUCCESS, labels={"database": "test_db"})
        collector.record_timer(StandardMetrics.QUERY_DURATION, 125.5, labels={"database": "test_db"})
        
        # Verify metrics were recorded
        assert collector.get_counter(StandardMetrics.QUERY_TOTAL) == 1.0
        assert collector.get_counter(
            StandardMetrics.QUERY_SUCCESS,
            labels={"database": "test_db"}
        ) == 1.0
        
        stats = collector.get_timer_stats(
            StandardMetrics.QUERY_DURATION,
            labels={"database": "test_db"}
        )
        assert stats is not None
        assert stats["avg_ms"] == 125.5


class TestFineGrainedMetricsControl:
    """Test fine-grained metrics collection control."""

    def test_query_metrics_disabled(self):
        """Test that query metrics are not collected when disabled."""
        collector = MetricsCollector(
            enabled=True,
            collect_query_metrics=False,
            collect_sql_metrics=True,
            collect_db_metrics=True,
        )
        
        # Try to collect query metrics
        collector.increment("mcp.query.total")
        collector.increment("mcp.query.success", labels={"database": "test"})
        collector.record_timer("mcp.query.duration", 100.0)
        
        # Verify no metrics were recorded
        assert collector.get_counter("mcp.query.total") == 0.0
        assert collector.get_counter("mcp.query.success", labels={"database": "test"}) == 0.0
        assert collector.get_timer_stats("mcp.query.duration") is None

    def test_sql_metrics_disabled(self):
        """Test that SQL metrics are not collected when disabled."""
        collector = MetricsCollector(
            enabled=True,
            collect_query_metrics=True,
            collect_sql_metrics=False,
            collect_db_metrics=True,
        )
        
        # Try to collect SQL metrics
        collector.increment("mcp.sql.generated")
        collector.record_timer("mcp.sql.generation_time", 50.0)
        
        # Verify no metrics were recorded
        assert collector.get_counter("mcp.sql.generated") == 0.0
        assert collector.get_timer_stats("mcp.sql.generation_time") is None

    def test_db_metrics_disabled(self):
        """Test that database metrics are not collected when disabled."""
        collector = MetricsCollector(
            enabled=True,
            collect_query_metrics=True,
            collect_sql_metrics=True,
            collect_db_metrics=False,
        )
        
        # Try to collect DB metrics
        collector.set_gauge("mcp.db.connections", 5.0)
        collector.increment("mcp.schema.cache_hits")
        collector.increment("mcp.validation.errors")
        
        # Verify no metrics were recorded
        assert collector.get_gauge("mcp.db.connections") is None
        assert collector.get_counter("mcp.schema.cache_hits") == 0.0
        assert collector.get_counter("mcp.validation.errors") == 0.0

    def test_selective_metrics_collection(self):
        """Test that only enabled metrics are collected."""
        collector = MetricsCollector(
            enabled=True,
            collect_query_metrics=True,
            collect_sql_metrics=False,
            collect_db_metrics=True,
        )
        
        # Collect various metrics
        collector.increment("mcp.query.total")  # Should be collected
        collector.increment("mcp.sql.generated")  # Should NOT be collected
        collector.set_gauge("mcp.db.connections", 3.0)  # Should be collected
        
        # Verify selective collection
        assert collector.get_counter("mcp.query.total") == 1.0
        assert collector.get_counter("mcp.sql.generated") == 0.0
        assert collector.get_gauge("mcp.db.connections") == 3.0

    def test_all_metrics_enabled(self):
        """Test that all metrics are collected when all flags are enabled."""
        collector = MetricsCollector(
            enabled=True,
            collect_query_metrics=True,
            collect_sql_metrics=True,
            collect_db_metrics=True,
        )
        
        # Collect all types of metrics
        collector.increment("mcp.query.total")
        collector.increment("mcp.sql.generated")
        collector.set_gauge("mcp.db.connections", 5.0)
        
        # Verify all were collected
        assert collector.get_counter("mcp.query.total") == 1.0
        assert collector.get_counter("mcp.sql.generated") == 1.0
        assert collector.get_gauge("mcp.db.connections") == 5.0

    def test_all_metrics_disabled_via_enabled_flag(self):
        """Test that no metrics are collected when enabled=False."""
        collector = MetricsCollector(
            enabled=False,
            collect_query_metrics=True,
            collect_sql_metrics=True,
            collect_db_metrics=True,
        )
        
        # Try to collect metrics
        collector.increment("mcp.query.total")
        collector.increment("mcp.sql.generated")
        collector.set_gauge("mcp.db.connections", 5.0)
        
        # Verify nothing was collected
        assert collector.get_counter("mcp.query.total") == 0.0
        assert collector.get_counter("mcp.sql.generated") == 0.0
        assert collector.get_gauge("mcp.db.connections") is None

    def test_metrics_without_category_prefix(self):
        """Test that metrics without known prefixes are always collected."""
        collector = MetricsCollector(
            enabled=True,
            collect_query_metrics=False,
            collect_sql_metrics=False,
            collect_db_metrics=False,
        )
        
        # Collect metrics without standard prefixes
        collector.increment("custom.metric")
        collector.set_gauge("another.gauge", 100.0)
        
        # Verify they are still collected (only when enabled=True)
        assert collector.get_counter("custom.metric") == 1.0
        assert collector.get_gauge("another.gauge") == 100.0

