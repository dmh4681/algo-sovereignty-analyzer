"""
Centralized Secrets Management Module

This module provides secure access to environment variables and secrets.
All sensitive configuration should be accessed through this module to ensure:
1. Consistent environment variable naming
2. Startup validation of required secrets
3. Clear error messages when secrets are missing
4. No hardcoded secrets in the codebase

Usage:
    from core.secrets import get_secret, validate_required_secrets, SecretConfig

    # Get a single secret (returns None if not found)
    api_key = get_secret("ANTHROPIC_API_KEY")

    # Get a secret with a default value
    node_url = get_secret("ALGORAND_NODE_URL", "https://mainnet-api.algonode.cloud")

    # Validate required secrets at startup (raises ValueError if missing)
    validate_required_secrets(["ANTHROPIC_API_KEY"])

Security Notes:
    - Never log or print secret values
    - Never include secrets in error messages
    - Use environment variables or a secure vault for all secrets
    - The .env file should never be committed to version control
"""

import os
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class SecretConfig:
    """Configuration for a secret/environment variable."""
    name: str
    description: str
    required: bool = False
    default: Optional[str] = None


# Registry of all known secrets used by the application
# This serves as documentation and enables startup validation
SECRETS_REGISTRY: Dict[str, SecretConfig] = {
    # Required for AI coaching feature
    "ANTHROPIC_API_KEY": SecretConfig(
        name="ANTHROPIC_API_KEY",
        description="API key for Anthropic Claude AI (required for coaching feature)",
        required=False,  # Only required if using coaching feature
        default=None
    ),

    # Algorand node configuration (optional - defaults to public node)
    "ALGORAND_NODE_URL": SecretConfig(
        name="ALGORAND_NODE_URL",
        description="URL for Algorand node API (default: AlgoNode public API)",
        required=False,
        default="https://mainnet-api.algonode.cloud"
    ),
    "ALGORAND_NODE_TOKEN": SecretConfig(
        name="ALGORAND_NODE_TOKEN",
        description="Authentication token for private Algorand node (not needed for AlgoNode)",
        required=False,
        default=""
    ),

    # CORS configuration
    "CORS_ORIGINS": SecretConfig(
        name="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins (default: * for development)",
        required=False,
        default="*"
    ),

    # FRED API (Federal Reserve Economic Data)
    "FRED_API_KEY": SecretConfig(
        name="FRED_API_KEY",
        description="API key for FRED (Federal Reserve Economic Data) — enables live CPI and M2 data",
        required=False,
        default=None
    ),

    # Algorand wallet mnemonic (only needed for deployment scripts, never for the API server)
    "ALGO_MNEMONIC": SecretConfig(
        name="ALGO_MNEMONIC",
        description="25-word Algorand mnemonic for NFT deployment scripts (NOT required for API server)",
        required=False,
        default=None
    ),

    # Database reseed flags (not secrets, but env config)
    "RESEED_MINERS": SecretConfig(
        name="RESEED_MINERS",
        description="Set to 'true' to reseed gold miner metrics database on startup",
        required=False,
        default="false"
    ),
    "RESEED_SILVER": SecretConfig(
        name="RESEED_SILVER",
        description="Set to 'true' to reseed silver miner metrics database on startup",
        required=False,
        default="false"
    ),
}


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve a secret/environment variable securely.

    Args:
        name: The environment variable name
        default: Default value if not found (overrides registry default)

    Returns:
        The secret value, or default if not found

    Security Note:
        This function never logs or prints the actual secret value.
    """
    value = os.environ.get(name)

    if value is not None:
        return value

    # Check if there's a default in the registry
    if name in SECRETS_REGISTRY and default is None:
        return SECRETS_REGISTRY[name].default

    return default


def validate_required_secrets(secret_names: List[str]) -> Dict[str, bool]:
    """
    Validate that required secrets are present in the environment.

    Args:
        secret_names: List of secret names to validate

    Returns:
        Dict mapping secret names to their presence status

    Raises:
        ValueError: If any required secrets are missing, with a helpful error message

    Security Note:
        Error messages never include the actual secret values.
    """
    results = {}
    missing = []

    for name in secret_names:
        value = os.environ.get(name)
        is_present = value is not None and value.strip() != ""
        results[name] = is_present

        if not is_present:
            missing.append(name)

    if missing:
        # Build helpful error message without exposing any values
        error_lines = [
            "Missing required environment variables:",
            ""
        ]

        for name in missing:
            if name in SECRETS_REGISTRY:
                desc = SECRETS_REGISTRY[name].description
                error_lines.append(f"  - {name}: {desc}")
            else:
                error_lines.append(f"  - {name}")

        error_lines.extend([
            "",
            "Please set these variables in your .env file or environment.",
            "See .env.example for reference."
        ])

        raise ValueError("\n".join(error_lines))

    return results


def get_algorand_node_config() -> tuple:
    """
    Get Algorand node configuration from environment.

    Returns:
        Tuple of (node_url, node_token, headers)

    The function returns appropriate configuration based on whether
    a custom node is configured or the public AlgoNode should be used.
    """
    node_url = get_secret("ALGORAND_NODE_URL", "https://mainnet-api.algonode.cloud")
    node_token = get_secret("ALGORAND_NODE_TOKEN", "")

    # Build headers based on whether we have a token
    if node_token:
        headers = {"Authorization": f"Bearer {node_token}"}
    else:
        headers = {}

    return node_url, node_token, headers


def check_optional_secrets() -> Dict[str, Dict[str, any]]:
    """
    Check the status of all registered secrets for diagnostics.

    Returns:
        Dict with secret status information (never includes actual values)

    This is useful for startup diagnostics and health checks.
    """
    status = {}

    for name, config in SECRETS_REGISTRY.items():
        value = os.environ.get(name)
        is_set = value is not None and value.strip() != ""

        status[name] = {
            "is_set": is_set,
            "required": config.required,
            "has_default": config.default is not None,
            "description": config.description
        }

    return status


def mask_secret(value: str, visible_chars: int = 4, strict: bool = False) -> str:
    """
    Mask a secret value for safe logging/display.

    Args:
        value: The secret value to mask
        visible_chars: Number of characters to show at start and end (default: 4)
        strict: If True, show only asterisks regardless of length (more secure)

    Returns:
        Masked string like "sk-a...y" or "****" for short/strict values

    Security Note:
        Use this when you need to log that a secret exists without exposing it.
        For highly sensitive secrets (API keys, tokens), consider using strict=True
        to avoid leaking any portion of the secret.

    Examples:
        mask_secret("sk-abcdefghijklmnop") -> "sk-a...nop"
        mask_secret("sk-abcdefghijklmnop", strict=True) -> "********"
        mask_secret("short") -> "****"
    """
    if not value:
        return "****"

    # Strict mode: never show any part of the secret
    if strict:
        return "*" * 8

    # For short values, show only asterisks (avoid partial exposure)
    if len(value) <= visible_chars * 2:
        return "*" * max(len(value), 4)

    return f"{value[:visible_chars]}...{value[-visible_chars:]}"
