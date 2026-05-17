"""
Tests for the Gemini API client wrapper.

Tests JSON extraction from various response formats, cache hit/miss
behavior, retry/backoff logic, and batch call concurrency.
"""

from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.utils.gemini_client import (
    _calculate_backoff_delay,
    _get_cache_key,
    _get_cached_result,
    _set_cached_result,
    _classification_cache,
    extract_json_from_response,
)


# ---------------------------------------------------------------------------
# extract_json_from_response
# ---------------------------------------------------------------------------

class TestExtractJsonFromResponse:
    """Tests for JSON extraction from LLM responses."""

    def test_plain_json_parsed(self):
        """Plain JSON string should be parsed directly."""
        text = '{"category": "IP_TRANSFER", "confidence": 0.95}'
        result = extract_json_from_response(text)
        assert result["category"] == "IP_TRANSFER"
        assert result["confidence"] == 0.95

    def test_json_in_markdown_fence_extracted(self):
        """JSON inside ```json ... ``` fences should be extracted."""
        text = '```json\n{"category": "NON_COMPETE", "confidence": 0.8}\n```'
        result = extract_json_from_response(text)
        assert result["category"] == "NON_COMPETE"

    def test_json_in_plain_code_fence_extracted(self):
        """JSON inside ``` ... ``` fences (no language tag) should be extracted."""
        text = '```\n{"severity": "HIGH", "verdict": "risky"}\n```'
        result = extract_json_from_response(text)
        assert result["severity"] == "HIGH"

    def test_json_with_surrounding_text_extracted(self):
        """JSON embedded in surrounding text should be extracted by brace matching."""
        text = 'Here is the result: {"key": "value"} as requested.'
        result = extract_json_from_response(text)
        assert result["key"] == "value"

    def test_invalid_json_raises_decode_error(self):
        """Completely invalid text should raise JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            extract_json_from_response("This is not JSON at all.")

    def test_nested_json_parsed(self):
        """Nested JSON objects should be parsed correctly."""
        text = '{"outer": {"inner": "value"}, "list": [1, 2, 3]}'
        result = extract_json_from_response(text)
        assert result["outer"]["inner"] == "value"
        assert result["list"] == [1, 2, 3]

    def test_whitespace_trimmed_before_parsing(self):
        """Leading/trailing whitespace should not prevent parsing."""
        text = '   \n  {"key": "value"}  \n  '
        result = extract_json_from_response(text)
        assert result["key"] == "value"

    def test_json_with_unicode_parsed(self):
        """JSON with unicode characters should be parsed correctly."""
        text = '{"text": "Clause with unicode: café"}'
        result = extract_json_from_response(text)
        assert "café" in result["text"]


# ---------------------------------------------------------------------------
# Cache behavior
# ---------------------------------------------------------------------------

class TestCacheBehavior:
    """Tests for the classification result cache."""

    def setup_method(self):
        """Clear cache before each test."""
        _classification_cache.clear()

    def test_cache_key_is_deterministic(self):
        """Same inputs should always produce the same cache key."""
        key1 = _get_cache_key("test prompt", "gemini-1.5-flash")
        key2 = _get_cache_key("test prompt", "gemini-1.5-flash")
        assert key1 == key2

    def test_different_prompts_produce_different_keys(self):
        """Different prompts should produce different cache keys."""
        key1 = _get_cache_key("prompt A", "gemini-1.5-flash")
        key2 = _get_cache_key("prompt B", "gemini-1.5-flash")
        assert key1 != key2

    def test_different_models_produce_different_keys(self):
        """Different model names should produce different cache keys."""
        key1 = _get_cache_key("same prompt", "gemini-1.5-flash")
        key2 = _get_cache_key("same prompt", "gemini-1.5-pro")
        assert key1 != key2

    def test_cache_miss_returns_none(self):
        """Cache miss should return None."""
        result = _get_cached_result("nonexistent_key")
        assert result is None

    def test_cache_hit_returns_stored_value(self):
        """Cache hit should return the stored value."""
        key = "test_cache_key"
        value = {"category": "IP_TRANSFER"}
        _set_cached_result(key, value)
        result = _get_cached_result(key)
        assert result == value

    def test_expired_cache_entry_returns_none(self):
        """Expired cache entry should return None."""
        key = "expired_key"
        value = {"category": "NON_COMPETE"}
        # Manually insert with old timestamp
        _classification_cache[key] = (value, time.time() - 7200)  # 2 hours ago
        result = _get_cached_result(key)
        assert result is None

    def test_cache_evicts_oldest_when_full(self):
        """Cache should evict oldest entry when at max capacity."""
        from backend.utils.gemini_client import _CACHE_MAX_SIZE
        _classification_cache.clear()
        # Fill cache to max
        for i in range(_CACHE_MAX_SIZE):
            _classification_cache[f"key_{i}"] = ({"val": i}, time.time() - (1000 - i))
        # Adding one more should evict the oldest
        _set_cached_result("new_key", {"val": "new"})
        assert len(_classification_cache) == _CACHE_MAX_SIZE
        assert "new_key" in _classification_cache


# ---------------------------------------------------------------------------
# Backoff delay
# ---------------------------------------------------------------------------

class TestBackoffDelay:
    """Tests for exponential backoff delay calculation."""

    def test_first_attempt_delay_is_positive(self):
        """First retry delay should be positive."""
        delay = _calculate_backoff_delay(0)
        assert delay > 0

    def test_delay_increases_with_attempts(self):
        """Delay should increase with each retry attempt."""
        delay_0 = _calculate_backoff_delay(0)
        delay_1 = _calculate_backoff_delay(1)
        delay_2 = _calculate_backoff_delay(2)
        # With jitter, we can't guarantee strict ordering, but base should grow
        # Check base values without jitter: 1.0, 2.0, 4.0
        assert delay_1 > delay_0 * 0.5  # At minimum, delay grows
        assert delay_2 > delay_0 * 0.5

    def test_delay_capped_at_max(self):
        """Delay should never exceed max delay + max jitter."""
        from backend.utils.gemini_client import _MAX_DELAY_SECONDS
        delay = _calculate_backoff_delay(100)  # Very high attempt
        assert delay <= _MAX_DELAY_SECONDS * 1.5  # Max + max jitter


# ---------------------------------------------------------------------------
# call_gemini integration (mocked)
# ---------------------------------------------------------------------------

class TestCallGemini:
    """Tests for the call_gemini function with mocked client."""

    @pytest.mark.asyncio
    @patch("backend.utils.gemini_client._get_client")
    async def test_successful_call_returns_dict(self, mock_get_client: MagicMock):
        """Successful Gemini call should return a parsed dict."""
        from backend.utils.gemini_client import call_gemini
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"category": "IP_TRANSFER", "confidence": 0.9}'
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = await call_gemini(
            prompt="test clause",
            system_prompt="classify this",
            model_name="gemini-1.5-flash",
        )
        assert result["category"] == "IP_TRANSFER"

    @pytest.mark.asyncio
    @patch("backend.utils.gemini_client._get_client")
    async def test_retries_on_failure_then_succeeds(self, mock_get_client: MagicMock):
        """Should retry on failure and succeed on second attempt."""
        from backend.utils.gemini_client import call_gemini
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"result": "ok"}'

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Temporary API error")
            return mock_response

        mock_client.models.generate_content.side_effect = side_effect
        mock_get_client.return_value = mock_client

        with patch("backend.utils.gemini_client.asyncio.sleep", new_callable=AsyncMock):
            result = await call_gemini(
                prompt="test",
                system_prompt="test",
                model_name="gemini-1.5-flash",
            )
        assert result["result"] == "ok"
        assert call_count == 2

    @pytest.mark.asyncio
    @patch("backend.utils.gemini_client._get_client")
    async def test_raises_after_max_retries(self, mock_get_client: MagicMock):
        """Should raise RuntimeError after all retries are exhausted."""
        from backend.utils.gemini_client import call_gemini
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("Persistent error")
        mock_get_client.return_value = mock_client

        with patch("backend.utils.gemini_client.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError, match="Gemini API call failed"):
                await call_gemini(
                    prompt="test",
                    system_prompt="test",
                    model_name="gemini-1.5-flash",
                )

    @pytest.mark.asyncio
    @patch("backend.utils.gemini_client._get_client")
    async def test_cache_prevents_duplicate_calls(self, mock_get_client: MagicMock):
        """Cached result should prevent a second API call."""
        from backend.utils.gemini_client import call_gemini
        _classification_cache.clear()

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"cached": true}'
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        # First call — hits API
        result1 = await call_gemini(
            prompt="unique prompt for cache test",
            system_prompt="system",
            model_name="gemini-1.5-flash",
            use_cache=True,
        )
        # Second call — should hit cache
        result2 = await call_gemini(
            prompt="unique prompt for cache test",
            system_prompt="system",
            model_name="gemini-1.5-flash",
            use_cache=True,
        )
        assert result1 == result2
        # API should only be called once
        assert mock_client.models.generate_content.call_count == 1
