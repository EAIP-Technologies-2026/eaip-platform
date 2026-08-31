"""Response transformer — field mapping, header modification, body filtering."""

from __future__ import annotations

import re
from typing import Any

from eaip.apiext.events import TransformApplied
from eaip.apiext.exceptions import TransformError
from eaip.apiext.models import ResponseTransform
from eaip.logging.context import get_logger


class ResponseTransformer:
    """Registers and applies response transformation rules."""

    def __init__(self) -> None:
        """Initialize the transformer with an empty registry."""
        self._transforms: dict[str, ResponseTransform] = {}
        self._log = get_logger("eaip.apiext.transforms")

    def register_transform(self, transform: ResponseTransform) -> None:
        """Register a new response transform.

        Args:
            transform: The transform definition.

        Raises:
            TransformError: If a transform with the same id already exists.
        """
        if transform.id in self._transforms:
            raise TransformError(
                f"Transform '{transform.id}' is already registered.",
                context={"transform_id": transform.id},
            )
        self._transforms[transform.id] = transform
        self._log.info(
            "apiext.transform.registered",
            transform_id=transform.id,
            endpoint_pattern=transform.endpoint_pattern,
        )

    def unregister_transform(self, transform_id: str) -> None:
        """Remove a previously registered transform.

        Args:
            transform_id: The transform identifier.

        Raises:
            TransformError: If the transform is not found.
        """
        if transform_id not in self._transforms:
            raise TransformError(
                f"Transform '{transform_id}' is not registered.",
                context={"transform_id": transform_id},
            )
        del self._transforms[transform_id]

    def list_transforms(self) -> list[ResponseTransform]:
        """Return all registered transforms.

        Returns:
            A list of all transforms.
        """
        return list(self._transforms.values())

    def get_transform(self, transform_id: str) -> ResponseTransform | None:
        """Look up a transform by identifier.

        Args:
            transform_id: The transform identifier.

        Returns:
            The matching transform, or ``None``.
        """
        return self._transforms.get(transform_id)

    async def apply_transforms(
        self,
        response: dict[str, Any],
        endpoint_path: str,
    ) -> dict[str, Any]:
        """Apply matching transforms to a response.

        Transforms are applied in priority order (descending).

        Args:
            response: The response dict to transform.
            endpoint_path: The endpoint path for matching.

        Returns:
            The transformed response.
        """
        matching = [
            t
            for t in self._transforms.values()
            if t.enabled and self._matches_pattern(endpoint_path, t.endpoint_pattern)
        ]
        matching.sort(key=lambda t: t.priority, reverse=True)

        result = dict(response)
        for transform in matching:
            result = self._apply_transform(result, transform)
            TransformApplied(
                transform_id=transform.id,
                transform_name=transform.name,
                endpoint_pattern=transform.endpoint_pattern,
                transformation_count=len(transform.transformations),
            )

        return result

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if a path matches a glob-like pattern.

        Supports ``*`` (any segment) and ``**`` (any depth).

        Args:
            path: The endpoint path.
            pattern: The glob pattern.

        Returns:
            ``True`` if the path matches.
        """
        regex = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]+")
        return bool(re.match(f"^{regex}$", path))

    def _apply_transform(
        self,
        response: dict[str, Any],
        transform: ResponseTransform,
    ) -> dict[str, Any]:
        """Apply a single transform to the response.

        Supports: ``rename_field``, ``remove_field``, ``set_header``,
        ``remove_header``, ``map_status``, ``filter_body``.

        Args:
            response: The response dict.
            transform: The transform to apply.

        Returns:
            The transformed response.
        """
        result = dict(response)

        for op in transform.transformations:
            parts = op.split(":", 2)
            command = parts[0]

            if command == "rename_field" and len(parts) == 3:
                old, new = parts[1], parts[2]
                if old in result.get("body", {}):
                    result["body"][new] = result["body"].pop(old)

            elif command == "remove_field" and len(parts) == 2:
                field = parts[1]
                result.get("body", {}).pop(field, None)

            elif command == "set_header" and len(parts) == 3:
                header_key, header_val = parts[1], parts[2]
                headers = result.get("headers", {})
                headers[header_key] = header_val
                result["headers"] = headers

            elif command == "remove_header" and len(parts) == 2:
                header_key = parts[1]
                headers = result.get("headers", {})
                headers.pop(header_key, None)
                result["headers"] = headers

            elif command == "map_status" and len(parts) == 3:
                old_status, new_status = int(parts[1]), int(parts[2])
                if result.get("status_code") == old_status:
                    result["status_code"] = new_status

            elif command == "filter_body" and len(parts) == 2:
                allowed = set(parts[1].split(","))
                body = result.get("body", {})
                result["body"] = {k: v for k, v in body.items() if k in allowed}

        return result


__all__ = ["ResponseTransformer"]
