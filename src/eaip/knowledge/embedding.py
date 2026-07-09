"""Embedding generation through the Provider Framework."""

from __future__ import annotations

import hashlib

from eaip.knowledge.exceptions import EmbeddingError
from eaip.knowledge.models import EmbeddingConfig
from eaip.logging.context import get_logger


class ProviderEmbedding:
    """Generates embeddings using the Provider Framework.

    Wraps a Provider that supports the EMBEDDING feature and
    delegates embedding calls through it.
    """

    def __init__(
        self,
        config: EmbeddingConfig,
        embed_fn: object | None = None,
    ) -> None:
        """Initialize ProviderEmbedding.

        Args:
            config: The embedding configuration.
            embed_fn: A callable that accepts list[str] and returns
                list[tuple[float, ...]]. If None, the embedding provider
                must be configured at runtime.
        """
        self._config = config
        self._embed_fn = embed_fn
        self._log = get_logger("eaip.knowledge.embedding")

    @property
    def dimensions(self) -> int:
        """Return the configured embedding dimension."""
        return self._config.dimensions

    async def embed(self, texts: list[str], **kwargs: str) -> list[tuple[float, ...]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: The texts to embed.
            **kwargs: Optional embedding parameters.

        Returns:
            A list of embedding vectors.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        if not texts:
            return []

        if self._embed_fn is None:
            raise EmbeddingError("No embedding function configured")

        self._log.debug(
            "embedding.start",
            batch_size=len(texts),
            dimensions=self._config.dimensions,
        )

        try:
            if callable(self._embed_fn):
                result = await self._embed_fn(texts, **kwargs)
            else:
                raise EmbeddingError("Configured embed_fn is not callable")

            vectors: list[tuple[float, ...]] = [tuple(v) for v in result]

            self._log.debug("embedding.complete", count=len(vectors))
            return vectors

        except EmbeddingError:
            raise
        except Exception as exc:
            self._log.error("embedding.failed", error=str(exc))
            raise EmbeddingError(f"Embedding generation failed: {exc}") from exc

    async def embed_batch(
        self, texts: list[str], batch_size: int | None = None, **kwargs: str
    ) -> list[tuple[float, ...]]:
        """Embed texts in batches to manage memory.

        Args:
            texts: The texts to embed.
            batch_size: Override batch size from config.
            **kwargs: Optional embedding parameters.

        Returns:
            A list of embedding vectors.
        """
        bs = batch_size or self._config.batch_size
        all_embeddings: list[tuple[float, ...]] = []

        for i in range(0, len(texts), bs):
            batch = texts[i : i + bs]
            embeddings = await self.embed(batch, **kwargs)
            all_embeddings.extend(embeddings)

        return all_embeddings


class MockEmbeddingProvider:
    """A mock embedding provider for testing.

    Generates deterministic embeddings of the configured dimension
    using a hash-based approach.
    """

    def __init__(self, dimensions: int = 384) -> None:
        """Initialize MockEmbeddingProvider.

        Args:
            dimensions: The embedding dimension.
        """
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        """Return the embedding dimension."""
        return self._dimensions

    async def embed(self, texts: list[str], **_kwargs: str) -> list[tuple[float, ...]]:
        """Generate deterministic embeddings.

        Args:
            texts: The texts to embed.

        Returns:
            A list of embedding vectors.
        """
        results: list[tuple[float, ...]] = []
        for text in texts:
            h = hashlib.sha256(text.encode()).digest()
            vec = [int(h[i % len(h)]) / 255.0 for i in range(self._dimensions)]
            results.append(tuple(vec))
        return results


__all__ = [
    "MockEmbeddingProvider",
    "ProviderEmbedding",
]
