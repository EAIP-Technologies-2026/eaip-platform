"""Tests for skillreg exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.skillreg.exceptions import SkillNotFoundError, SkillRegistryError


class TestSkillRegistryError:
    def test_base_exception(self) -> None:
        err = SkillRegistryError("Registry error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_with_context(self) -> None:
        err = SkillRegistryError("Error", context={"skill_id": "s1"})
        assert err.context == {"skill_id": "s1"}


class TestSkillNotFoundError:
    def test_default_code(self) -> None:
        err = SkillNotFoundError("Not found")
        assert isinstance(err, SkillRegistryError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = SkillNotFoundError("Skill 's1' not found")
        assert "s1" in str(err)
