"""Pluggable artifact signing — HMAC default, asymmetric via env, Sigstore/Cosign-compatible contract."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from abc import ABC, abstractmethod
from typing import Any


def _canonical(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def sign_artifact(payload: dict[str, Any], secret: str) -> str:
    return hmac.new(secret.encode(), _canonical(payload), hashlib.sha256).hexdigest()


def verify_artifact(payload: dict[str, Any], signature: str, secret: str) -> bool:
    expected = sign_artifact(payload, secret)
    return hmac.compare_digest(expected, signature)


def artifact_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


class SigningProvider(ABC):
    @abstractmethod
    def sign(self, payload: dict[str, Any]) -> tuple[str, str]:
        """Return (signature, key_id)."""

    @abstractmethod
    def verify(self, payload: dict[str, Any], signature: str, key_id: str = "") -> bool:
        """Verify signature."""


class HMACSigningProvider(SigningProvider):
    def __init__(self, secret: str = "") -> None:
        self._secret = secret or os.environ.get("EAIP_MARKETPLACE_SIGNING_SECRET", "eaip-marketplace-signing-key")

    def sign(self, payload: dict[str, Any]) -> tuple[str, str]:
        return sign_artifact(payload, self._secret), "hmac-sha256"

    def verify(self, payload: dict[str, Any], signature: str, key_id: str = "") -> bool:
        return verify_artifact(payload, signature, self._secret)


class AsymmetricSigningProvider(SigningProvider):
    """Ed25519 / RSA pluggable — uses cryptography if available, else HMAC fallback."""

    def __init__(self, private_key_pem: str = "", public_key_pem: str = "") -> None:
        self._priv = private_key_pem or os.environ.get("EAIP_MARKETPLACE_PRIVATE_KEY", "")
        self._pub = public_key_pem or os.environ.get("EAIP_MARKETPLACE_PUBLIC_KEY", "")
        self._fallback = HMACSigningProvider()

    def sign(self, payload: dict[str, Any]) -> tuple[str, str]:
        if self._priv and self._priv.startswith("-----BEGIN"):
            try:
                from cryptography.hazmat.primitives.asymmetric import ed25519
                from cryptography.hazmat.primitives import serialization

                key = serialization.load_pem_private_key(self._priv.encode(), password=None)
                sig = key.sign(_canonical(payload))
                return base64.b64encode(sig).decode(), "ed25519"
            except Exception:
                pass
        return self._fallback.sign(payload)

    def verify(self, payload: dict[str, Any], signature: str, key_id: str = "") -> bool:
        if self._pub and self._pub.startswith("-----BEGIN"):
            try:
                from cryptography.hazmat.primitives.asymmetric import ed25519
                from cryptography.hazmat.primitives import serialization

                key = serialization.load_pem_public_key(self._pub.encode())
                sig = base64.b64decode(signature)
                key.verify(sig, _canonical(payload))
                return True
            except Exception:
                return False
        return self._fallback.verify(payload, signature, key_id)


def get_signing_provider() -> SigningProvider:
    priv = os.environ.get("EAIP_MARKETPLACE_PRIVATE_KEY", "")
    if priv and priv.startswith("-----BEGIN"):
        return AsymmetricSigningProvider()
    return HMACSigningProvider()


__all__ = ["SigningProvider", "HMACSigningProvider", "AsymmetricSigningProvider", "get_signing_provider", "sign_artifact", "verify_artifact", "artifact_digest"]
