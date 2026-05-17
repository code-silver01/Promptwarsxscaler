"""
Gemini API client wrapper with retry logic and structured JSON parsing.

Implements exponential backoff with jitter for all Gemini API calls,
LRU caching for classification results, and strict JSON extraction.
Uses the google-genai SDK (latest recommended package).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import random
import re
import time
from typing import Any, Optional

from google import genai
from google.genai import types

logger = logging.getLogger("lexguard.gemini_client")

# Cache for classification results — TTL managed manually
_classification_cache: dict[str, tuple[Any, float]] = {}
_CACHE_TTL_SECONDS: int = 3600  # 1 hour
_CACHE_MAX_SIZE: int = 500

# Retry configuration
_MAX_RETRIES: int = 3
_BASE_DELAY_SECONDS: float = 1.0
_MAX_DELAY_SECONDS: float = 30.0

# Module-level client
_client: Optional[genai.Client] = None


def initialize_gemini(api_key: Optional[str] = None) -> None:
    """
    Configure the Gemini client with the provided API key.

    Args:
        api_key: Gemini API key. Falls back to GEMINI_API_KEY env var.

    Raises:
        ValueError: If no API key is available.
    """
    global _client
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY must be set via environment variable "
            "or passed directly"
        )
    _client = genai.Client(api_key=key)
    logger.info("Gemini SDK initialized successfully")


def _get_client() -> genai.Client:
    """
    Get the initialized Gemini client.

    Returns:
        Configured genai.Client.

    Raises:
        RuntimeError: If client not initialized.
    """
    global _client
    if _client is None:
        key = os.environ.get("GEMINI_API_KEY")
        if key:
            _client = genai.Client(api_key=key)
        else:
            raise RuntimeError("Gemini client not initialized. Call initialize_gemini() first.")
    return _client


def _get_cache_key(prompt: str, model_name: str) -> str:
    """
    Generate a deterministic cache key from prompt and model.

    Args:
        prompt: The full prompt text.
        model_name: Gemini model identifier.

    Returns:
        SHA-256 hex digest as cache key.
    """
    content = f"{model_name}:{prompt}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _get_cached_result(cache_key: str) -> Optional[Any]:
    """
    Retrieve a cached result if it exists and hasn't expired.

    Args:
        cache_key: The cache key to look up.

    Returns:
        Cached result or None if not found or expired.
    """
    if cache_key in _classification_cache:
        result, timestamp = _classification_cache[cache_key]
        if time.time() - timestamp < _CACHE_TTL_SECONDS:
            logger.debug("Cache hit for key %s", cache_key[:12])
            return result
        del _classification_cache[cache_key]
    return None


def _set_cached_result(cache_key: str, result: Any) -> None:
    """
    Store a result in the cache with current timestamp.

    Evicts oldest entries if cache exceeds max size.

    Args:
        cache_key: The cache key.
        result: The result to cache.
    """
    if len(_classification_cache) >= _CACHE_MAX_SIZE:
        oldest_key = min(
            _classification_cache, key=lambda k: _classification_cache[k][1]
        )
        del _classification_cache[oldest_key]
    _classification_cache[cache_key] = (result, time.time())


def _calculate_backoff_delay(attempt: int) -> float:
    """
    Calculate exponential backoff delay with jitter.

    Args:
        attempt: Zero-indexed retry attempt number.

    Returns:
        Delay in seconds before next retry.
    """
    delay = min(
        _BASE_DELAY_SECONDS * (2 ** attempt),
        _MAX_DELAY_SECONDS,
    )
    jitter = random.uniform(0, delay * 0.5)
    return delay + jitter


def extract_json_from_response(text: str) -> dict:
    """
    Extract JSON from an LLM response, handling markdown fences.

    Args:
        text: Raw text response from the LLM.

    Returns:
        Parsed JSON dictionary.

    Raises:
        json.JSONDecodeError: If no valid JSON can be extracted.
    """
    cleaned = text.strip()

    # Try direct JSON parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fences
    fence_pattern = re.compile(
        r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL
    )
    match = fence_pattern.search(cleaned)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding JSON object boundaries
    brace_start = cleaned.find("{")
    brace_end = cleaned.rfind("}")
    if brace_start != -1 and brace_end != -1:
        try:
            return json.loads(cleaned[brace_start : brace_end + 1])
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError(
        "No valid JSON found in response", cleaned, 0
    )


async def call_gemini(
    prompt: str,
    system_prompt: str,
    model_name: str = "gemini-2.5-pro",
    use_cache: bool = False,
    temperature: float = 0.3,
) -> dict:
    """
    Call the Gemini API with retry logic and optional caching.

    Args:
        prompt: User message content (clause text).
        system_prompt: System instruction for the model.
        model_name: Gemini model to use.
        use_cache: Whether to cache the result (for classification).
        temperature: Sampling temperature.

    Returns:
        Parsed JSON dictionary from the model response.

    Raises:
        RuntimeError: If all retry attempts fail.
    """
    cache_key = _get_cache_key(
        f"{system_prompt}|{prompt}", model_name
    ) if use_cache else None

    if cache_key:
        cached = _get_cached_result(cache_key)
        if cached is not None:
            return cached

    client = _get_client()
    last_error: Optional[Exception] = None
    start_time = time.time()

    for attempt in range(_MAX_RETRIES):
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            )
            result = extract_json_from_response(response.text)

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                json.dumps({
                    "service": "gemini_client",
                    "operation": "call_gemini",
                    "model": model_name,
                    "attempt": attempt + 1,
                    "duration_ms": round(duration_ms, 2),
                    "status": "success",
                })
            )

            if cache_key:
                _set_cached_result(cache_key, result)

            return result

        except Exception as exc:
            last_error = exc
            delay = _calculate_backoff_delay(attempt)
            logger.warning(
                json.dumps({
                    "service": "gemini_client",
                    "operation": "call_gemini",
                    "model": model_name,
                    "attempt": attempt + 1,
                    "status": "retry",
                    "error": str(exc),
                    "backoff_seconds": round(delay, 2),
                })
            )
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(delay)

    duration_ms = (time.time() - start_time) * 1000
    logger.error(
        json.dumps({
            "service": "gemini_client",
            "operation": "call_gemini",
            "model": model_name,
            "status": "failed",
            "duration_ms": round(duration_ms, 2),
            "error": str(last_error),
        })
    )
    raise RuntimeError(
        f"Gemini API call failed after {_MAX_RETRIES} attempts: "
        f"{last_error}"
    )


async def call_gemini_batch(
    prompts: list[tuple[str, str]],
    model_name: str = "gemini-2.5-flash",
    use_cache: bool = True,
    temperature: float = 0.2,
    max_concurrency: int = 5,
) -> list[dict]:
    """
    Call Gemini for multiple prompts with concurrency control.

    Args:
        prompts: List of (user_prompt, system_prompt) tuples.
        model_name: Gemini model to use.
        use_cache: Whether to cache results.
        temperature: Sampling temperature.
        max_concurrency: Maximum concurrent API calls.

    Returns:
        List of parsed JSON dictionaries in input order.
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _bounded_call(
        user_prompt: str, sys_prompt: str
    ) -> dict:
        async with semaphore:
            return await call_gemini(
                prompt=user_prompt,
                system_prompt=sys_prompt,
                model_name=model_name,
                use_cache=use_cache,
                temperature=temperature,
            )

    tasks = [
        _bounded_call(user_prompt, sys_prompt)
        for user_prompt, sys_prompt in prompts
    ]
    return await asyncio.gather(*tasks)
