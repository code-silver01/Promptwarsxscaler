"""
Google Cloud Storage client for temporary document uploads in LexGuard One.
"""
from __future__ import annotations
import json
import logging
import os
import uuid
from typing import Optional

logger = logging.getLogger("lexguard.gcs_client")

_gcs_client = None


def _get_gcs_client():
    """Get or create the GCS client singleton."""
    global _gcs_client
    if _gcs_client is None:
        from google.cloud import storage
        _gcs_client = storage.Client()
    return _gcs_client


async def upload_document(file_content: bytes, filename: str) -> Optional[str]:
    """
    Upload document bytes to GCS for temporary storage.

    Args:
        file_content: Raw file bytes to upload.
        filename: Original filename for extension detection.

    Returns:
        GCS blob URI (gs://bucket/path) or None if upload fails.
    """
    bucket_name = os.environ.get("GCS_BUCKET")
    if not bucket_name:
        logger.warning(json.dumps({
            "service": "gcs_client", "operation": "upload_document",
            "status": "skipped", "reason": "GCS_BUCKET not configured",
        }))
        return None

    try:
        import asyncio
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        blob_name = f"uploads/{uuid.uuid4().hex}.{ext}"

        def _upload():
            client = _get_gcs_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(file_content, content_type="application/octet-stream")
            return f"gs://{bucket_name}/{blob_name}"

        uri = await asyncio.to_thread(_upload)
        logger.info(json.dumps({
            "service": "gcs_client", "operation": "upload_document",
            "uri": uri, "status": "success",
        }))
        return uri

    except Exception as exc:
        logger.error(json.dumps({
            "service": "gcs_client", "operation": "upload_document",
            "status": "error", "error": str(exc),
        }))
        return None


async def delete_document(gcs_uri: str) -> None:
    """
    Delete a document from GCS after processing.

    Args:
        gcs_uri: GCS URI (gs://bucket/blob) to delete.
    """
    if not gcs_uri or not gcs_uri.startswith("gs://"):
        return
    try:
        import asyncio
        parts = gcs_uri[5:].split("/", 1)
        bucket_name, blob_name = parts[0], parts[1]

        def _delete():
            client = _get_gcs_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()

        await asyncio.to_thread(_delete)
        logger.info(json.dumps({
            "service": "gcs_client", "operation": "delete_document",
            "uri": gcs_uri, "status": "success",
        }))
    except Exception as exc:
        logger.warning(json.dumps({
            "service": "gcs_client", "operation": "delete_document",
            "uri": gcs_uri, "status": "error", "error": str(exc),
        }))
