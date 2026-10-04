import subprocess
import sys
from unittest.mock import MagicMock, patch
import pytest
import httpx

from app.core.config import Settings
from app.services.embedding.api import APIEmbeddingProvider, get_api_embedding_provider
from app.services.embedding.local import LocalEmbeddingProvider, get_local_embedding_provider, get_embedding_provider


def test_api_provider_configuration():
    provider = APIEmbeddingProvider(
        api_url="https://example.com/embed",
        api_key="secret-token-test",
        timeout=15.0,
    )
    assert provider.dimension == 384
    assert provider.api_url == "https://example.com/embed"
    assert provider.api_key == "secret-token-test"
    headers = provider._get_headers()
    assert headers["Authorization"] == "Bearer secret-token-test"
    assert headers["Content-Type"] == "application/json"
    provider.close()


def test_api_provider_no_auth_header_when_no_key():
    provider = APIEmbeddingProvider(api_url="https://example.com/embed", api_key="")
    headers = provider._get_headers()
    assert "Authorization" not in headers
    provider.close()


def test_api_provider_embed_text_empty_returns_zero_vector():
    provider = APIEmbeddingProvider(api_url="https://example.com/embed", api_key="key")
    # Empty string should not trigger HTTP request
    vec = provider.embed_text("")
    assert len(vec) == 384
    assert all(x == 0.0 for x in vec)

    vec_whitespace = provider.embed_text("   ")
    assert len(vec_whitespace) == 384
    assert all(x == 0.0 for x in vec_whitespace)
    provider.close()


def test_api_provider_embed_text_success_1d():
    provider = APIEmbeddingProvider(api_url="https://example.com/embed", api_key="key")
    fake_vector = [0.1] * 384

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_vector

    with patch.object(provider._client, "post", return_value=mock_resp) as mock_post:
        result = provider.embed_text("Teeth whitening pricing")
        assert len(result) == 384
        assert result[0] == 0.1
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"] == {"inputs": "Teeth whitening pricing"}
    provider.close()


def test_api_provider_embed_text_success_2d():
    provider = APIEmbeddingProvider(api_url="https://example.com/embed", api_key="key")
    fake_vector = [[0.25] * 384]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_vector

    with patch.object(provider._client, "post", return_value=mock_resp):
        result = provider.embed_text("Opening hours")
        assert len(result) == 384
        assert result[0] == 0.25
    provider.close()


def test_api_provider_embed_batch_success():
    provider = APIEmbeddingProvider(api_url="https://example.com/embed", api_key="key")
    fake_batch = [
        [0.1] * 384,
        [0.2] * 384,
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_batch

    with patch.object(provider._client, "post", return_value=mock_resp) as mock_post:
        result = provider.embed_batch(["Question 1", "Question 2"])
        assert len(result) == 2
        assert len(result[0]) == 384
        assert len(result[1]) == 384
        assert result[0][0] == 0.1
        assert result[1][0] == 0.2
        mock_post.assert_called_once()
    provider.close()


def test_api_provider_dimension_validation_single():
    provider = APIEmbeddingProvider(api_url="https://example.com/embed", api_key="key")
    # Wrong dimension: 512 instead of 384
    fake_vector = [0.1] * 512

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_vector

    with patch.object(provider._client, "post", return_value=mock_resp):
        with pytest.raises(ValueError, match="Embedding dimension mismatch: expected 384, but API returned 512"):
            provider.embed_text("Query")
    provider.close()


def test_api_provider_dimension_validation_batch():
    provider = APIEmbeddingProvider(api_url="https://example.com/embed", api_key="key")
    # Batch index 1 has wrong dimension
    fake_batch = [
        [0.1] * 384,
        [0.1] * 256,
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_batch

    with patch.object(provider._client, "post", return_value=mock_resp):
        with pytest.raises(ValueError, match="Embedding dimension mismatch at batch index 1"):
            provider.embed_batch(["Text 1", "Text 2"])
    provider.close()


def test_api_provider_http_error_handling_no_silent_fallback():
    provider = APIEmbeddingProvider(api_url="https://example.com/embed", api_key="key")

    # 401 Unauthorized
    mock_401 = MagicMock()
    mock_401.status_code = 401
    mock_401.text = '{"error": "Invalid token"}'

    with patch.object(provider._client, "post", return_value=mock_401):
        with pytest.raises(RuntimeError, match="Embedding API returned status 401"):
            provider.embed_text("Testing error")

    # 503 Model Loading
    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_503.text = '{"error": "Model is currently loading"}'

    with patch.object(provider._client, "post", return_value=mock_503):
        with pytest.raises(RuntimeError, match="Embedding API returned status 503"):
            provider.embed_text("Testing error")

    provider.close()


def test_api_provider_network_failure():
    provider = APIEmbeddingProvider(api_url="https://example.com/embed", api_key="key")

    with patch.object(provider._client, "post", side_effect=httpx.ConnectError("Network unreachable")):
        with pytest.raises(RuntimeError, match="Embedding API connection failed"):
            provider.embed_text("Testing error")
    provider.close()


def test_embedding_factory_selection():
    # 1. When EMBEDDING_PROVIDER=api
    with patch("app.services.embedding.local.settings.EMBEDDING_PROVIDER", "api"):
        provider = get_embedding_provider()
        assert isinstance(provider, APIEmbeddingProvider)
        assert provider.dimension == 384

    # 2. When EMBEDDING_PROVIDER=local
    with patch("app.services.embedding.local.settings.EMBEDDING_PROVIDER", "local"):
        provider = get_embedding_provider()
        assert isinstance(provider, LocalEmbeddingProvider)
        assert provider.dimension == 384


def test_local_provider_still_works():
    local_provider = get_local_embedding_provider()
    assert isinstance(local_provider, LocalEmbeddingProvider)
    assert local_provider.dimension == 384
    # Empty string check runs without loading model
    assert len(local_provider.embed_text("")) == 384
    assert len(local_provider.embed_batch([])) == 0


def test_no_torch_imported_when_api_provider():
    """Verify that importing app and getting API provider in a clean process does NOT import torch or sentence_transformers."""
    code = """
import sys
import os

# Set environment variable to api
os.environ["EMBEDDING_PROVIDER"] = "api"
os.environ["EMBEDDING_API_KEY"] = "dummy_token"

from app.services.embedding import get_embedding_provider
provider = get_embedding_provider()
assert provider.dimension == 384

# Verify that neither torch nor sentence_transformers is imported into memory
assert "torch" not in sys.modules, f"torch was imported! sys.modules keys: {[k for k in sys.modules if 'torch' in k]}"
assert "sentence_transformers" not in sys.modules, "sentence_transformers was imported!"

print("CLEAN_IMPORT_SUCCESS")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd="backend",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Subprocess failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    assert "CLEAN_IMPORT_SUCCESS" in result.stdout
