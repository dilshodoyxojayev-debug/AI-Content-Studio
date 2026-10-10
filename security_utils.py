"""Helpers for keeping API credentials out of user-visible error messages."""

import re


_QUERY_SECRET_PATTERN = re.compile(
    r"([?&](?:key|api_key|apikey)=)[^&\s]+",
    re.IGNORECASE,
)


def redact_sensitive_text(value, *secrets) -> str:
    """Redact known secret values and common API-key query parameters."""
    message = str(value)
    for secret in secrets:
        if secret:
            message = message.replace(str(secret), "[REDACTED]")
    return _QUERY_SECRET_PATTERN.sub(r"\1[REDACTED]", message)
