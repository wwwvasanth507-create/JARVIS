"""
Test Suite for Phase 12: Final Packaging, Release & Deployment.

Validates:
1. Package version consistency and programmatic access (myllm.version and myllm.__version__)
2. Model manifest schema, checksum format, and model entries
3. Model verification function (verify_model) on smoke checkpoint
4. API /ready readiness probe schema and response
5. Strict CPU enforcement (rejection of non-CPU devices)
6. Dockerfile and docker-compose.yml existence and configuration
7. Frontend .env.example documentation
8. Release manifest completeness
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

import myllm
from myllm.api.app import create_app
from myllm.api.service import APIService
from myllm.config import ModelConfig, ServerConfig
from myllm.model.gpt import GPTModel
from myllm.tokenizer import Tokenizer
from myllm.utils.device import DeviceNotAllowedError, resolve_device
from scripts.verify_model import verify_model

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_package_version_accessibility():
    """Verify package version is defined and accessible via both attributes."""
    assert hasattr(myllm, "__version__")
    assert hasattr(myllm, "version")
    assert myllm.__version__ == "0.1.0"
    assert myllm.version == "0.1.0"


def test_model_manifest_integrity():
    """Verify model_manifest.json contains valid entries and checksums."""
    manifest_path = REPO_ROOT / "model_manifest.json"
    assert manifest_path.is_file(), "model_manifest.json is missing"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "manifest_version" in data
    assert "models" in data
    assert len(data["models"]) >= 2

    for m in data["models"]:
        assert "model_name" in m
        assert "checkpoint_path" in m
        assert "checkpoint_sha256" in m
        assert len(m["checkpoint_sha256"]) == 64  # SHA-256 hex length
        assert "tokenizer_path" in m
        assert "tokenizer_sha256" in m
        assert len(m["tokenizer_sha256"]) == 64
        assert "tokenizer_fingerprint" in m
        assert m["cpu_compatibility"]["strict_cpu_only"] is True


def test_smoke_model_verification():
    """Verify programmatic verification function passes on smoke model."""
    ckpt_path = REPO_ROOT / "checkpoints" / "smoke" / "best.pt"
    tok_path = REPO_ROOT / "checkpoints" / "smoke" / "tokenizer.json"
    manifest_path = REPO_ROOT / "model_manifest.json"

    if not ckpt_path.is_file() or not tok_path.is_file():
        pytest.skip("Smoke model artifacts not present")

    passed = verify_model(ckpt_path, tok_path, manifest_path)
    assert passed is True


def test_api_readiness_probe():
    """Verify GET /ready returns 200 and valid schema when model is loaded."""
    tok_path = REPO_ROOT / "checkpoints" / "smoke" / "tokenizer.json"
    if tok_path.is_file():
        tokenizer = Tokenizer.load(tok_path)
    else:
        tokenizer = Tokenizer()

    config = ModelConfig(
        vocab_size=len(tokenizer),
        context_length=32,
        n_layer=1,
        n_head=2,
        n_embd=16,
    )
    model = GPTModel(config)
    server_cfg = ServerConfig(checkpoint="dummy.pt", tokenizer="dummy.json")
    service = APIService(model=model, tokenizer=tokenizer, config=server_cfg)

    app = create_app(service=service)
    client = TestClient(app)

    # Health probe
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    # Readiness probe
    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    data = res_ready.json()
    assert data["status"] == "ready"
    assert data["ready"] is True
    assert data["model_loaded"] is True
    assert data["device"] == "cpu"
    assert data["parameter_count"] > 0
    assert data["context_length"] == 32


def test_strict_cpu_enforcement():
    """Verify non-CPU devices are strictly rejected under strict_cpu policy."""
    # cpu is allowed
    dev = resolve_device("cpu", strict_cpu=True)
    assert dev.type == "cpu"

    # cuda must raise DeviceNotAllowedError
    with pytest.raises(DeviceNotAllowedError):
        resolve_device("cuda", strict_cpu=True)

    with pytest.raises(DeviceNotAllowedError):
        resolve_device("cuda:0", strict_cpu=True)


def test_docker_configuration_artifacts():
    """Verify Dockerfile, .dockerignore, and docker-compose.yml exist and specify CPU."""
    dockerfile = REPO_ROOT / "Dockerfile"
    dockerignore = REPO_ROOT / ".dockerignore"
    compose = REPO_ROOT / "docker-compose.yml"

    assert dockerfile.is_file(), "Dockerfile is missing"
    assert dockerignore.is_file(), ".dockerignore is missing"
    assert compose.is_file(), "docker-compose.yml is missing"

    content = dockerfile.read_text(encoding="utf-8")
    assert "https://download.pytorch.org/whl/cpu" in content
    assert "EXPOSE 8000" in content


def test_frontend_env_example():
    """Verify frontend/.env.example documents VITE_API_URL."""
    env_example = REPO_ROOT / "frontend" / ".env.example"
    assert env_example.is_file(), "frontend/.env.example is missing"
    content = env_example.read_text(encoding="utf-8")
    assert "VITE_API_URL=" in content


def test_release_manifest_validity():
    """Verify release_manifest.json contains release metadata."""
    manifest = REPO_ROOT / "release_manifest.json"
    assert manifest.is_file(), "release_manifest.json is missing"
    data = json.loads(manifest.read_text(encoding="utf-8"))

    assert data["release_version"] == "0.1.0"
    assert data["environment"]["strict_cpu_mode"] is True
    assert data["environment"]["cuda_used"] is False
    assert "primary_release_model" in data["models"]
