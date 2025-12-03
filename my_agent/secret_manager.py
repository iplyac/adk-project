"""Helpers for loading secrets from Google Secret Manager.

This module centralizes access to GSM so that services can populate
environment variables (e.g., API keys) at startup without committing
credentials to the repository or .env files.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from google.cloud import secretmanager


def _build_secret_name(secret_id: str, project_id: str, version: str) -> str:
    """Return a fully-qualified secret version name.

    If ``secret_id`` already looks like a fully-qualified resource path it is
    returned as-is. Otherwise, the function builds the path using the provided
    project identifier.
    """

    if secret_id.startswith("projects/"):
        return secret_id
    return f"projects/{project_id}/secrets/{secret_id}/versions/{version}"


def get_secret_value(
    secret_id: str,
    *,
    project_id: Optional[str] = None,
    version: str = "latest",
) -> str:
    """Fetch a secret value from Google Secret Manager.

    Args:
        secret_id: Secret identifier or fully-qualified secret version name.
        project_id: Optional project ID. If ``secret_id`` is not fully
            qualified, this value (or the ``GCP_PROJECT_ID`` environment
            variable) is used to build the resource name.
        version: Secret version; defaults to ``latest``.

    Returns:
        The decoded secret payload.
    """

    resolved_project_id = project_id or os.getenv("GCP_PROJECT_ID")
    if not resolved_project_id and not secret_id.startswith("projects/"):
        raise ValueError("project_id or GCP_PROJECT_ID is required to access secrets")

    name = _build_secret_name(secret_id, resolved_project_id, version)
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("utf-8")


def load_secret_into_env(
    env_var: str,
    secret_env_var: str,
    *,
    project_id: Optional[str] = None,
    version: str = "latest",
    logger: Optional[logging.Logger] = None,
) -> None:
    """Populate an environment variable from Google Secret Manager.

    The function is a no-op if ``env_var`` is already set. Otherwise, it looks
    for ``secret_env_var`` to find the secret ID and loads the secret into the
    process environment.
    """

    if os.getenv(env_var):
        return

    secret_id = os.getenv(secret_env_var)
    if not secret_id:
        return

    try:
        value = get_secret_value(secret_id, project_id=project_id, version=version)
        os.environ[env_var] = value
        if logger:
            logger.info("Loaded %s from Secret Manager secret %s", env_var, secret_id)
    except Exception as exc:  # pragma: no cover - defensive logging only
        if logger:
            logger.error("Failed to load secret for %s: %s", env_var, exc)
        else:
            raise
