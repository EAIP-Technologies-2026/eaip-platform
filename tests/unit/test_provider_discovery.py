from __future__ import annotations

from eaip.providers.discovery import ProviderDiscovery
from eaip.providers.models import ProviderInstance, ProviderStatus
from eaip.providers.registry import ProviderRegistry


class TestProviderDiscovery:
    def test_register_instance(self) -> None:
        registry = ProviderRegistry()
        discovery = ProviderDiscovery(registry)
        inst = ProviderInstance(name="ollama", provider_type="ollama",
                                 endpoint="http://localhost:11434")
        discovery.register_instance(inst)
        assert registry.get("ollama") == inst

    def test_discover_from_config(self) -> None:
        registry = ProviderRegistry()
        discovery = ProviderDiscovery(registry)
        configs = [
            {"name": "ollama", "provider_type": "ollama",
             "endpoint": "http://localhost:11434", "default_model": "llama3"},
            {"name": "nvidia", "provider_type": "nvidia",
             "endpoint": "https://api.nvidia.com/v1", "api_key": "test-key"},
        ]
        instances = discovery.discover_from_config(configs)
        assert len(instances) == 2
        assert registry.get("ollama").default_model == "llama3"
        assert registry.get("nvidia").api_key == "test-key"

    def test_discovered_instances_have_unavailable_status(self) -> None:
        registry = ProviderRegistry()
        discovery = ProviderDiscovery(registry)
        configs = [{"name": "test", "provider_type": "openai_compat",
                     "endpoint": "http://test"}]
        instances = discovery.discover_from_config(configs)
        assert instances[0].status is ProviderStatus.UNAVAILABLE
