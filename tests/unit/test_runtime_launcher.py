"""Tests for Runtime Launcher v3 — non-blocking backend launch protocol.

Verifies the core invariants from AI_RUNTIME_GUARDRAILS.md §L:
  - RL-1: Never wait for python -m eaip to exit
  - RL-2: Launch backend detached
  - RL-3: Poll /health every 1s (60s timeout)
  - RL-4: On HTTP 200 from /health, continue immediately
  - RL-5: Poll /ready until HTTP 200
  - RL-7: Timeout produces root-cause report
  - RL-8: Never block on long-running server process
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

WORKSPACE = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS_DIR = WORKSPACE / "scripts"
EAIP_DEV_JS = SCRIPTS_DIR / "eaip-dev.js"


def _read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _node_eval(expr: str) -> Any:
    command = (
        f"const m = require('{EAIP_DEV_JS.as_posix()}'); "
        f"process.stdout.write(JSON.stringify({expr}))"
    )
    result = subprocess.run(
        ["node", "-e", command],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(WORKSPACE),
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Node eval failed: {result.stderr}")
    return json.loads(result.stdout)


def _node_call(fn: str, *args: Any) -> Any:
    args_json = json.dumps(list(args))
    command = (
        f"const m = require('{EAIP_DEV_JS.as_posix()}'); "
        f"(async () => {{ const r = await m.{fn}(...{args_json}); "
        "process.stdout.write(JSON.stringify(r)); })()"
    )
    result = subprocess.run(
        ["node", "-e", command],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(WORKSPACE),
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Node call {fn} failed: {result.stderr}")
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Test: httpGet returns structured response
# ---------------------------------------------------------------------------
class TestHttpGet:
    def test_returns_ok_false_for_unreachable(self) -> None:
        result = _node_call("httpGet", "http://127.0.0.1:19999/health", 2000)
        assert isinstance(result, dict)
        assert "ok" in result
        assert "statusCode" in result
        assert result["ok"] is False

    def test_returns_ok_true_for_live_endpoint(self) -> None:
        try:
            r = subprocess.run(
                [
                    "node",
                    "-e",
                    (
                        f"const m = require('{EAIP_DEV_JS.as_posix()}'); "
                        "(async () => { "
                        "  const r = await m.httpGet('http://127.0.0.1:8080/health', 3000); "
                        "  process.stdout.write(JSON.stringify(r)); "
                        "})()"
                    ),
                ],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(WORKSPACE),
                check=False,
            )
            result = json.loads(r.stdout)
            if result.get("ok"):
                body = json.loads(result["body"])
                assert "status" in body
                assert body["status"] in ("healthy", "degraded")
        except (json.JSONDecodeError, FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("Backend not running on :8080")


# ---------------------------------------------------------------------------
# Test: Health polling with bounded timeout (RL-3, RL-8)
# ---------------------------------------------------------------------------
class TestHealthPolling:
    """Verify health polling respects timeout and never hangs."""

    def test_poll_loop_terminates_within_timeout(self) -> None:
        """A polling loop against an unreachable host must terminate, not hang."""
        start = time.monotonic()
        elapsed = 0.0
        timeout_s = 3
        while elapsed < timeout_s:
            result = _node_call("httpGet", "http://127.0.0.1:19999/health", 1000)
            assert result["ok"] is False
            elapsed = time.monotonic() - start
            time.sleep(0.2)
        # Total should be roughly timeout_s, never more than 2x
        assert elapsed < timeout_s * 2, f"Polling took {elapsed:.1f}s, expected ~{timeout_s}s"

    def test_polling_uses_bounded_http_timeout(self) -> None:
        """Each httpGet call must have a finite timeout, not block indefinitely."""
        result = _node_call("httpGet", "http://127.0.0.1:19999/health", 2000)
        assert isinstance(result, dict)
        assert "ok" in result


# ---------------------------------------------------------------------------
# Test: Backend spawn is detached (RL-2)
# ---------------------------------------------------------------------------
class TestBackendSpawnDetached:
    def test_spawn_returns_immediately(self) -> None:
        result = subprocess.run(
            [
                "node",
                "-e",
                (
                    f"const m = require('{EAIP_DEV_JS.as_posix()}'); "
                    "const child = m.spawnCommand('node', ['-e', 'setTimeout(() => {}, 60000)'], "
                    "{ stdio: ['ignore', 'pipe', 'pipe'] }); "
                    "process.stdout.write(JSON.stringify({"
                    "  hasPid: !!child.pid,"
                    "  pidType: typeof child.pid,"
                    "  killed: child.killed,"
                    "  exitCode: child.exitCode"
                    "})); "
                    "child.kill(); "
                ),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(WORKSPACE),
            check=False,
        )
        info = json.loads(result.stdout)
        assert info["hasPid"] is True
        assert info["pidType"] == "number"
        assert info["killed"] is False
        assert info["exitCode"] is None


# ---------------------------------------------------------------------------
# Test: parseDotenv correctly loads .env files
# ---------------------------------------------------------------------------
class TestParseDotenv:
    def test_parses_basic_key_value(self) -> None:
        result = _node_call("parseDotenv", "FOO=bar\nBAZ=qux")
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_skips_comments(self) -> None:
        result = _node_call("parseDotenv", "# comment\nFOO=bar\n# another\nBAZ=qux")
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_handles_quoted_values(self) -> None:
        result = _node_call("parseDotenv", "FOO=\"hello world\"\nBAR='test value'")
        assert result["FOO"] == "hello world"
        assert result["BAR"] == "test value"

    def test_handles_export_prefix(self) -> None:
        result = _node_call("parseDotenv", "export FOO=bar")
        assert result == {"FOO": "bar"}

    def test_skips_empty_lines(self) -> None:
        result = _node_call("parseDotenv", "\n\nFOO=bar\n\n\n")
        assert result == {"FOO": "bar"}


# ---------------------------------------------------------------------------
# Test: loadEnvFiles merges multiple files
# ---------------------------------------------------------------------------
class TestLoadEnvFiles:
    def test_loads_existing_files(self) -> None:
        backend_dir = WORKSPACE / "eaip-platform"
        result = _node_call("loadEnvFiles", str(backend_dir), [".env", ".env.local"])
        assert isinstance(result, dict)
        if (backend_dir / ".env").exists():
            assert "EAIP_AUTH_SECRET" in result

    def test_missing_files_ignored(self) -> None:
        result = _node_call("loadEnvFiles", str(WORKSPACE), ["nonexistent.env"])
        assert result == {}


# ---------------------------------------------------------------------------
# Test: pidsOnPort returns array
# ---------------------------------------------------------------------------
class TestPidsOnPort:
    def test_returns_array_for_free_port(self) -> None:
        result = _node_call("pidsOnPort", 19999)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_returns_pids_for_used_port(self) -> None:
        result = _node_call("pidsOnPort", 8080)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Test: isPortInUse returns boolean
# ---------------------------------------------------------------------------
class TestIsPortInUse:
    def test_returns_boolean(self) -> None:
        result = _node_call("isPortInUse", 19999)
        assert isinstance(result, bool)
        assert result is False

    def test_detects_used_port(self) -> None:
        result = _node_call("isPortInUse", 8080)
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Test: backendHealthOnPort returns correct shape
# ---------------------------------------------------------------------------
class TestBackendHealthOnPort:
    def test_returns_health_shape(self) -> None:
        result = _node_call("backendHealthOnPort", 19999)
        assert isinstance(result, dict)
        assert "present" in result
        assert "healthy" in result
        assert result["present"] is False
        assert result["healthy"] is False

    def test_detects_healthy_backend(self) -> None:
        result = _node_call("backendHealthOnPort", 8080)
        assert isinstance(result, dict)
        assert "present" in result
        assert "healthy" in result
        if result["present"]:
            assert "isEaip" in result


# ---------------------------------------------------------------------------
# Test: extractPortFromOutput parses frontend port
# ---------------------------------------------------------------------------
class TestExtractPortFromOutput:
    def test_extracts_local_url_port(self) -> None:
        result = _node_call("extractPortFromOutput", "  Local: http://localhost:3001")
        assert result == 3001

    def test_extracts_any_url_port(self) -> None:
        result = _node_call("extractPortFromOutput", "Ready on http://127.0.0.1:3002")
        assert result == 3002

    def test_returns_null_for_no_url(self) -> None:
        result = _node_call("extractPortFromOutput", "Compiling...")
        assert result is None


# ---------------------------------------------------------------------------
# Test: REPOSITORIES registry
# ---------------------------------------------------------------------------
class TestRepositoryRegistry:
    def test_has_backend_repo(self) -> None:
        repos = _node_eval("m.REPOSITORIES.filter(r => r.kind === 'backend')")
        assert len(repos) == 1
        backend = repos[0]
        assert backend["name"] == "eaip-platform"
        assert backend["role"] == "runtime"
        assert "healthPath" in backend
        assert backend["healthPath"] == "/health"

    def test_has_frontend_repo(self) -> None:
        repos = _node_eval("m.REPOSITORIES.filter(r => r.kind === 'frontend')")
        assert len(repos) >= 1
        frontend = repos[0]
        assert frontend["name"] == "eaip-frontend"
        assert frontend["role"] == "runtime"

    def test_design_repos_are_not_runtime(self) -> None:
        repos = _node_eval("m.REPOSITORIES.filter(r => r.role === 'design')")
        for repo in repos:
            assert repo["role"] == "design"
            assert "kind" in repo
            assert repo["kind"] in ("docs", "design")


# ---------------------------------------------------------------------------
# Test: .env file exists with EAIP_AUTH_SECRET
# ---------------------------------------------------------------------------
class TestEnvFileExists:
    def test_env_file_has_auth_secret(self) -> None:
        env_path = WORKSPACE / "eaip-platform" / ".env"
        if not env_path.exists():
            pytest.skip(".env file not found")

        content = _read_utf8(env_path)
        assert "EAIP_AUTH_SECRET=" in content

        for line in content.splitlines():
            if line.strip().startswith("EAIP_AUTH_SECRET="):
                value = line.split("=", 1)[1].strip()
                assert value != "change-this-to-a-long-random-secret-for-development"
                assert len(value) >= 32
                break


class TestLoadDotenvInMain:
    def test_load_dotenv_import_present(self) -> None:
        main_path = WORKSPACE / "eaip-platform" / "src" / "eaip" / "__main__.py"
        if not main_path.exists():
            pytest.skip("__main__.py not found")

        content = _read_utf8(main_path)
        assert "load_dotenv" in content
        assert "from dotenv import load_dotenv" in content


# ---------------------------------------------------------------------------
# Test: Start-EAIP.ps1 exists and has correct structure
# ---------------------------------------------------------------------------
class TestStartEAIPScript:
    def _read(self) -> str:
        return _read_utf8(SCRIPTS_DIR / "Start-EAIP.ps1")

    def test_script_exists(self) -> None:
        assert (SCRIPTS_DIR / "Start-EAIP.ps1").exists()

    def test_has_health_polling(self) -> None:
        content = self._read()
        assert "/health" in content
        assert "BackendHealthTimeout" in content or "HealthTimeout" in content

    def test_has_ready_polling(self) -> None:
        assert "/ready" in self._read()

    def test_has_timeout_report(self) -> None:
        content = self._read()
        assert "BLOCKED" in content
        assert "timeout" in content.lower() or "Timeout" in content

    def test_never_waits_on_process_exit(self) -> None:
        content = self._read()
        assert "WaitForExit" not in content

    def test_has_ready_banner(self) -> None:
        assert "Backend READY" in self._read()


# ---------------------------------------------------------------------------
# Test: Stop-EAIP.ps1 exists and has correct structure
# ---------------------------------------------------------------------------
class TestStopEAIPScript:
    def _read(self) -> str:
        return _read_utf8(SCRIPTS_DIR / "Stop-EAIP.ps1")

    def test_script_exists(self) -> None:
        assert (SCRIPTS_DIR / "Stop-EAIP.ps1").exists()

    def test_has_orphan_detection(self) -> None:
        content = self._read()
        assert "orphan" in content.lower() or "Orphan" in content

    def test_has_state_cleanup(self) -> None:
        content = self._read()
        assert "runtime.json" in content or "StateFile" in content


# ---------------------------------------------------------------------------
# Test: Guardrails document has section L
# ---------------------------------------------------------------------------
class TestGuardrailsSectionL:
    def _read(self) -> str:
        return _read_utf8(WORKSPACE / "ai" / "playbooks" / "AI_RUNTIME_GUARDRAILS.md")

    def test_section_l_exists(self) -> None:
        guardrails_path = WORKSPACE / "ai" / "playbooks" / "AI_RUNTIME_GUARDRAILS.md"
        if not guardrails_path.exists():
            pytest.skip("AI_RUNTIME_GUARDRAILS.md not found")
        assert "## L. Runtime Launcher v3" in self._read()

    def test_has_rl_rules(self) -> None:
        content = self._read()
        for rule in ["RL-1", "RL-2", "RL-3", "RL-7", "RL-8"]:
            assert rule in content

    def test_never_wait_rule(self) -> None:
        content = self._read()
        assert "never wait" in content.lower()
