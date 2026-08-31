from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.filestore.exceptions import (
    DuplicateFileError,
    FileNotFoundError,
    FileStoreError,
    FileTooLargeError,
    StorageProviderError,
    UnsupportedFileTypeError,
)


class TestFilestoreExceptions:
    def test_base(self) -> None:
        err = FileStoreError("base")
        assert err.code == ErrorCode.UNKNOWN

    def test_file_not_found(self) -> None:
        err = FileNotFoundError("not found", context={"asset_id": "a1"})
        assert err.code == ErrorCode.NOT_FOUND
        assert err.context["asset_id"] == "a1"

    def test_file_too_large(self) -> None:
        err = FileTooLargeError("too large", context={"size": 1000, "max_size": 500})
        assert err.code == ErrorCode.VALIDATION_FAILED
        assert err.context["size"] == 1000

    def test_unsupported_file_type(self) -> None:
        err = UnsupportedFileTypeError("bad type", context={"content_type": "exe"})
        assert err.code == ErrorCode.VALIDATION_FAILED
        assert err.context["content_type"] == "exe"

    def test_storage_provider_error(self) -> None:
        err = StorageProviderError("provider down", context={"provider": "s3"})
        assert err.code == ErrorCode.PROVIDER_UNAVAILABLE
        assert err.context["provider"] == "s3"

    def test_duplicate_file(self) -> None:
        err = DuplicateFileError("duplicate", context={"hash": "abc123"})
        assert err.code == ErrorCode.REGISTRY_DUPLICATE
        assert err.context["hash"] == "abc123"

    def test_with_cause(self) -> None:
        cause = ValueError("root cause")
        err = FileStoreError("msg", cause=cause)
        assert err.__cause__ is cause

    def test_to_dict(self) -> None:
        err = FileNotFoundError("missing", context={"asset_id": "a1"})
        d = err.to_dict()
        assert d["type"] == "FileNotFoundError"
        assert d["code"] == "EAIP-0003"
        assert d["context"]["asset_id"] == "a1"

    def test_inheritance(self) -> None:
        assert issubclass(FileNotFoundError, FileStoreError)
        assert issubclass(FileTooLargeError, FileStoreError)
        assert issubclass(UnsupportedFileTypeError, FileStoreError)
        assert issubclass(StorageProviderError, FileStoreError)
        assert issubclass(DuplicateFileError, FileStoreError)
