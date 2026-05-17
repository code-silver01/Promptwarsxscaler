"""
Google Secret Manager client for LexGuard One.
Falls back to environment variables in local development.
"""
from __future__ import annotations
import json
import logging
import os
from typing import Optional

logger = logging.getLogger("lexguard.secret_manager")


def get_secret(secret_id: str, version: str = "latest") -> Optional[str]:
    """
    Retrieve a secret from Google Secret Manager.
    Falls back to os.environ for local development.

    Args:
        secret_id: The Secret Manager secret ID (e.g. "GEMINI_API_KEY").
        version: Secret version, defaults to "latest".

    Returns:
        Secret value string, or None if not found.
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    
    # Local development: use environment variables directly
    env_value = os.environ.get(secret_id)
    if not project_id:
        return env_value

    # GCP: try Secret Manager, fall back to env var
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})
        value = response.payload.data.decode("UTF-8")
        logger.info(json.dumps({
            "service": "secret_manager",
            "operation": "get_secret",
            "secret_id": secret_id,
            "status": "success",
        }))
        return value
    except Exception as exc:
        logger.warning(json.dumps({
            "service": "secret_manager",
            "operation": "get_secret",
            "secret_id": secret_id,
            "status": "fallback_to_env",
            "reason": str(exc),
        }))
        return env_value
