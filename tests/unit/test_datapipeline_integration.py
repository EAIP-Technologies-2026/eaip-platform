from __future__ import annotations

from eaip.datapipeline.integration import PipelineRuntimeModule
from eaip.datapipeline.models import PipelineConfig


class TestPipelineRuntimeModule:
    def test_module_name(self) -> None:
        module = PipelineRuntimeModule()
        assert module.name == "datapipeline"

    def test_default_config(self) -> None:
        module = PipelineRuntimeModule()
        assert module._config.max_records_per_run == 10000
        assert module._config.default_batch_size == 100

    def test_custom_config(self) -> None:
        config = PipelineConfig(max_records_per_run=5000, default_batch_size=50)
        module = PipelineRuntimeModule(config=config)
        assert module._config.max_records_per_run == 5000
        assert module._config.default_batch_size == 50

    def test_engine_property(self) -> None:
        module = PipelineRuntimeModule()
        assert module.engine is not None

    def test_engine_with_custom_config(self) -> None:
        config = PipelineConfig(max_records_per_run=5000)
        module = PipelineRuntimeModule(config=config)
        assert module.engine._config.max_records_per_run == 5000
