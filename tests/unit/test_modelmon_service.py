"""Tests for ModelMonitor service."""

from __future__ import annotations

import pytest

from eaip.modelmon.exceptions import ModelNotFoundError
from eaip.modelmon.models import DriftMetric, ModelMetrics, MonitorConfig
from eaip.modelmon.monitor import ModelMonitor


class TestModelMonitor:
    @pytest.fixture
    def monitor(self) -> ModelMonitor:
        return ModelMonitor()

    @pytest.fixture
    def configured_monitor(self) -> ModelMonitor:
        config = MonitorConfig(drift_threshold=0.05, degradation_threshold=0.02)
        return ModelMonitor(config=config)

    @pytest.fixture
    def sample_metrics(self) -> ModelMetrics:
        return ModelMetrics(
            model_id="model-1",
            version="1.0.0",
            accuracy=0.95,
            precision=0.94,
            recall=0.93,
            f1_score=0.935,
            latency_ms=42.0,
            sample_count=1000,
        )

    class TestTrackVersion:
        async def test_track_new_version(self, monitor: ModelMonitor) -> None:
            await monitor.track_version("model-1", "1.0.0")
            tracked = await monitor.list_tracked_models()
            assert len(tracked) == 1
            assert tracked[0][0] == "model-1"
            assert "1.0.0" in tracked[0][1]

        async def test_track_duplicate_version(self, monitor: ModelMonitor) -> None:
            await monitor.track_version("model-1", "1.0.0")
            await monitor.track_version("model-1", "1.0.0")
            tracked = await monitor.list_tracked_models()
            assert len(tracked[0][1]) == 1

        async def test_track_multiple_versions(self, monitor: ModelMonitor) -> None:
            await monitor.track_version("model-1", "1.0.0")
            await monitor.track_version("model-1", "2.0.0")
            tracked = await monitor.list_tracked_models()
            assert len(tracked[0][1]) == 2

    class TestRecordMetrics:
        async def test_record_metrics(
            self, monitor: ModelMonitor, sample_metrics: ModelMetrics
        ) -> None:
            await monitor.track_version("model-1", "1.0.0")
            result = await monitor.record_metrics("model-1", "1.0.0", sample_metrics)
            assert result.model_id == "model-1"
            assert result.accuracy == 0.95

        async def test_record_multiple_metrics(
            self, monitor: ModelMonitor, sample_metrics: ModelMetrics
        ) -> None:
            await monitor.track_version("model-1", "1.0.0")
            await monitor.record_metrics("model-1", "1.0.0", sample_metrics)
            m2 = sample_metrics.model_copy(update={"accuracy": 0.92})
            await monitor.record_metrics("model-1", "1.0.0", m2)
            metrics = await monitor.get_metrics("model-1")
            assert len(metrics) == 2

        async def test_get_metrics_empty(self, monitor: ModelMonitor) -> None:
            metrics = await monitor.get_metrics("nonexistent")
            assert metrics == []

    class TestDetectDrift:
        async def test_no_drift_when_baseline_only(self, monitor: ModelMonitor) -> None:
            await monitor.track_version("model-1", "1.0.0")
            metrics = ModelMetrics(
                model_id="model-1",
                version="1.0.0",
                accuracy=0.95,
                precision=0.95,
                recall=0.95,
                f1_score=0.95,
                latency_ms=10.0,
                sample_count=500,
            )
            await monitor.record_metrics("model-1", "1.0.0", metrics)
            report = await monitor.detect_drift("model-1", "1.0.0")
            assert not report.is_drifted

        async def test_drift_detected(self, monitor: ModelMonitor) -> None:
            await monitor.track_version("model-1", "1.0.0")
            m1 = ModelMetrics(
                model_id="model-1",
                version="1.0.0",
                accuracy=0.95,
                precision=0.95,
                recall=0.95,
                f1_score=0.95,
                latency_ms=10.0,
                sample_count=500,
            )
            m2 = ModelMetrics(
                model_id="model-1",
                version="1.0.0",
                accuracy=0.70,
                precision=0.95,
                recall=0.95,
                f1_score=0.95,
                latency_ms=10.0,
                sample_count=500,
            )
            await monitor.record_metrics("model-1", "1.0.0", m1)
            await monitor.record_metrics("model-1", "1.0.0", m2)
            report = await monitor.detect_drift("model-1", "1.0.0")
            assert report.is_drifted
            assert report.drift_metric == DriftMetric.MODEL

        async def test_drift_report_fields(self, monitor: ModelMonitor) -> None:
            await monitor.track_version("model-1", "1.0.0")
            m1 = ModelMetrics(
                model_id="model-1",
                version="1.0.0",
                accuracy=0.95,
                precision=0.95,
                recall=0.95,
                f1_score=0.95,
                latency_ms=10.0,
                sample_count=500,
            )
            m2 = ModelMetrics(
                model_id="model-1",
                version="1.0.0",
                accuracy=0.80,
                precision=0.95,
                recall=0.95,
                f1_score=0.95,
                latency_ms=10.0,
                sample_count=500,
            )
            await monitor.record_metrics("model-1", "1.0.0", m1)
            await monitor.record_metrics("model-1", "1.0.0", m2)
            report = await monitor.detect_drift("model-1", "1.0.0")
            assert report.model_id == "model-1"
            assert report.version == "1.0.0"
            assert report.threshold == 0.1
            assert report.drift_score > 0

        async def test_drift_not_detected_below_threshold(
            self, configured_monitor: ModelMonitor
        ) -> None:
            await configured_monitor.track_version("model-1", "1.0.0")
            m1 = ModelMetrics(
                model_id="model-1",
                version="1.0.0",
                accuracy=0.95,
                precision=0.95,
                recall=0.95,
                f1_score=0.95,
                latency_ms=10.0,
                sample_count=500,
            )
            m2 = ModelMetrics(
                model_id="model-1",
                version="1.0.0",
                accuracy=0.93,
                precision=0.95,
                recall=0.95,
                f1_score=0.95,
                latency_ms=10.0,
                sample_count=500,
            )
            await configured_monitor.record_metrics("model-1", "1.0.0", m1)
            await configured_monitor.record_metrics("model-1", "1.0.0", m2)
            report = await configured_monitor.detect_drift("model-1", "1.0.0")
            assert not report.is_drifted

    class TestDetectDriftErrors:
        async def test_model_not_found(self, monitor: ModelMonitor) -> None:
            with pytest.raises(ModelNotFoundError):
                await monitor.detect_drift("nonexistent", "1.0.0")

        async def test_no_metrics_recorded(self, monitor: ModelMonitor) -> None:
            await monitor.track_version("model-1", "1.0.0")
            with pytest.raises(ModelNotFoundError):
                await monitor.detect_drift("model-1", "1.0.0")

    class TestCheckDegradation:
        async def test_degradation_detected(self, configured_monitor: ModelMonitor) -> None:
            await configured_monitor.track_version("model-1", "1.0.0")
            m1 = ModelMetrics(
                model_id="model-1",
                version="1.0.0",
                accuracy=0.95,
                precision=0.95,
                recall=0.95,
                f1_score=0.95,
                latency_ms=10.0,
                sample_count=500,
            )
            m2 = ModelMetrics(
                model_id="model-1",
                version="1.0.0",
                accuracy=0.90,
                precision=0.95,
                recall=0.95,
                f1_score=0.95,
                latency_ms=10.0,
                sample_count=500,
            )
            await configured_monitor.record_metrics("model-1", "1.0.0", m1)
            await configured_monitor.record_metrics("model-1", "1.0.0", m2)
            degraded = await configured_monitor.check_degradation("model-1", "1.0.0")
            assert degraded

        async def test_no_degradation(self, configured_monitor: ModelMonitor) -> None:
            await configured_monitor.track_version("model-1", "1.0.0")
            m1 = ModelMetrics(
                model_id="model-1",
                version="1.0.0",
                accuracy=0.95,
                precision=0.95,
                recall=0.95,
                f1_score=0.95,
                latency_ms=10.0,
                sample_count=500,
            )
            await configured_monitor.record_metrics("model-1", "1.0.0", m1)
            degraded = await configured_monitor.check_degradation("model-1", "1.0.0")
            assert not degraded

        async def test_degradation_error_no_model(self, monitor: ModelMonitor) -> None:
            with pytest.raises(ModelNotFoundError):
                await monitor.check_degradation("nonexistent", "1.0.0")

    class TestListTrackedModels:
        async def test_empty(self, monitor: ModelMonitor) -> None:
            tracked = await monitor.list_tracked_models()
            assert tracked == []

        async def test_multiple_models(self, monitor: ModelMonitor) -> None:
            await monitor.track_version("model-a", "1.0")
            await monitor.track_version("model-b", "2.0")
            tracked = await monitor.list_tracked_models()
            assert len(tracked) == 2

    class TestConfig:
        def test_default_config(self) -> None:
            monitor = ModelMonitor()
            assert monitor.config.drift_threshold == 0.1
            assert monitor.config.evaluation_interval_seconds == 3600

        def test_custom_config(self) -> None:
            config = MonitorConfig(drift_threshold=0.2, max_metrics_history=500)
            monitor = ModelMonitor(config=config)
            assert monitor.config.drift_threshold == 0.2
            assert monitor.config.max_metrics_history == 500

        def test_config_frozen(self) -> None:
            config = MonitorConfig()
            with pytest.raises(Exception):
                config.drift_threshold = 0.5
