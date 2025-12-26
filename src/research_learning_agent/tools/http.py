from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from typing import Any, TypeVar, cast

import requests
from requests import Response
from urllib.parse import urlsplit, urlunsplit

from ..logging_utils import get_logger

logger = get_logger("tools.http")


# ---------------------------------
# Error types
# ---------------------------------

@dataclass
class ToolHTTPError(Exception):
    """Normalized HTTP error with status code and message for tool HTTP calls."""
    error_type: str              # "timeout" / "network" / "http" / "parse" / "unexpected" / "config"
    message: str
    status_code: int | None = None
    url: str | None = None
    response_text: str | None = None

    # ---- safe accessors ----

    @property
    def safe_url(self) -> str | None:
        return _sanitize_url(self.url)

    @property
    def safe_response_text(self) -> str | None:
        return _truncate(self.response_text)
    
    # ---- string representation ----
    
    def __str__(self) -> str:
        base = f"{self.error_type} error: {self.message}"
        if self.status_code is not None:
            base += f" (status={self.status_code})"
        if self.safe_url:
            base += f" (url={self.safe_url})"
        return base


# ---------------------------------
# Config helpers
# ---------------------------------

_T = TypeVar("_T", int, float)

def _env_number(name: str, default: _T, parse_type: type[_T] = int) -> _T:
    """Get an environment variable as a number (int or float), returning default if missing or invalid.
    
    Args:
        name: Environment variable name
        default: Default value to return if env var is missing/invalid
        parse_type: Type to parse as (int or float). Defaults to int.
    
    Returns:
        The parsed number or default value
    """
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return cast(_T, parse_type(raw))
    except ValueError:
        return default

def _env_int(name: str, default: int) -> int:
    """Get an environment variable as an int, returning default if missing or invalid."""
    return _env_number(name, default, int)

def _env_float(name: str, default: float) -> float:
    """Get an environment variable as a float, returning default if missing or invalid."""
    return _env_number(name, default, float)

def _bool_env(name: str, default: bool = False) -> bool:
    """Get an environment variable as a boolean, returning default if missing or invalid."""
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


DEFAULT_TIMEOUT_SECONDS = _env_float("TOOL_TIMEOUT_SECONDS", 12.0)
DEFAULT_MAX_RETRIES = _env_int("TOOL_MAX_RETRIES", 2)

# Off by default. Enable locally only if needed.
LOG_HTTP_REDACTED_BODY = _bool_env("LOG_HTTP_REDACTED_BODY", default=False)

# Backoof settings (keep conservative for Days 4)
BACKOFF_BASE_SECONDS = 0.6
BACKOFF_MAX_SECONDS = 6.0

_MAX_TEXT_LEN = 500


# ---------------------------------
# Logging safety helpers
# ---------------------------------
SENSITIVE_KEY_SUBSTRINGS = (
    "authorization", "api_key", "apikey", "x-api-key", "token",
    "access_token", "resfresh_token", "client_secret", "password", "secret"
)

def _truncate(text: str | None, limit: int = _MAX_TEXT_LEN) -> str | None:
    if not text:
        return None
    return text[:limit]

def _sanitize_url(url: str) -> str:
    """Drop query string to avoid leaking secrets in URL params."""
    try:
        parts = urlsplit(url)
        return urlunsplit((parts.schema, parts.netloc, parts.path, "", ""))  # no query/fragment
    except Exception:
        return url

def _redect_obj(obj: object) -> object:
    """Recursively redact sensitive values in dicts/lists based on key substrings."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            ks = str(k).lower()
            if any(s in ks for s in SENSITIVE_KEY_SUBSTRINGS):
                out[k] = "***REDACTED***"
            else:
                out[k] = _redect_obj(v)
        return out
    if isinstance(obj, list):
        return [_redect_obj(v) for v in obj]
    return obj

def _safe_json_keys(json_body: object, limit: int = 25) -> list[str] | None:
    """Return a list of safe JSON keys, sorted alphabetically, up to limit."""
    if isinstance(json_body, dict):
        keys = [str(k) for k in json_body.keys()]
        keys.sort()
        return keys[:limit]
    return None

def _safe_params_keys(params: object, limit: int = 25) -> list[str] | None:
    """Return a list of safe URL params keys, sorted alphabetically, up to limit."""
    if isinstance(params, dict):
        keys = [str(k) for k in params.keys()]
        keys.sort()
        return keys[:limit]
    return None

def _safe_body_preview(json_body: object, limit_chars: int = 400) -> str | None:
    """Return a redected, truncated JSON string if enabled by env."""
    if not LOG_HTTP_REDACTED_BODY or json_body is None:
        return None
    try:
        safe = _redect_obj(json_body)
        return json.dumps(safe)[:limit_chars]
    except Exception:
        return "<unserializable json_body>"


# ---------------------------------
# Retry policy
# ---------------------------------

def _is_retryable_status(status_code: int) -> bool:
    # 429 (rate limit), and transient server errors (5xx)
    return status_code in (429, 500, 502, 503, 504)

def _sleep_backoff(attempt: int) -> None:
    # Exponential backoff with jitter
    expo = BACKOFF_BASE_SECONDS * (2 ** attempt)
    jitter = random.uniform(0.0, 0.25 * expo)
    delay = min(BACKOFF_MAX_SECONDS, expo + jitter)
    time.sleep(delay)


# ---------------------------------
# Core request helpers
# ---------------------------------

def _safe_text(resp: Response, limit: int = 2000) -> str:
    """Safely extract response text, returning truncated version if parsing fails."""
    try:
        t = resp.text or ""
        return t[:limit]
    except Exception:
        return f"<failed to parse response text (len={len(resp.text)})>"


def request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    data: Any | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Response:
    """
    Make an HTTP request with retries + timeouts.
    Returns a `requests.Response` object if successful; otherwise raises ToolHTTPError.

    Retries:
      - network erros
      - timeouts
      - HTTP 429/5xx (retryable errors)
    """
    method_u = method.upper().strip()
    if method_u not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
        raise ToolHTTPError(
            error_type="unexpected",
            message=f"Unsupported method: {method}",
            url=url,
        )

    last_exc: Exception | None = None

    for attempt in range(max_retries):
        try:
            logger.debug(
                "HTTP %s %s attempt=%d/%d params_keys=%s json_keys=%s json_preview=%s",
                method_u,
                _sanitize_url(url),
                attempt + 1,
                max_retries,
                _safe_params_keys(params),
                _safe_json_keys(json_body),
                _safe_body_preview(json_body),     
            )

            resp = requests.request(
                method=method_u,
                url=url,
                headers=headers,
                params=params,
                json=json_body,
                data=data,
                timeout=timeout_seconds,
            )

            # Retryable HTTP errors
            if _is_retryable_status(resp.status_code):
                msg = f"Retryable HTTP status: {resp.status_code}"
                logger.warning("%s for %s (attempt=%d/%d)", msg, url, attempt + 1, max_retries)
                if attempt < max_retries:
                    _sleep_backoff(attempt)
                    continue
                raise ToolHTTPError(
                    error_type="http",
                    message=msg,
                    status_code=resp.status_code,
                    url=url,
                    response_text=_safe_text(resp),
                )
            
            # Non-retryable HTTP errors
            if resp.status_code >= 400:
                raise ToolHTTPError(
                    error_type="http",
                    message=f"HTTP error {resp.status_code}",
                    status_code=resp.status_code,
                    url=url,
                    response_text=_safe_text(resp),
                )

            # Success
            return resp

        except requests.Timeout as e:
            last_exc = e
            logger.warning("Timeout calling %s (attempt=%d/%d)", url, attempt + 1, max_retries)
            if attempt < max_retries:
                _sleep_backoff(attempt)
                continue
            raise ToolHTTPError(error_type="timeout", message=str(e), url=url) from e
        
        except requests.RequestException as e:
            # Covers connection errors, DNS errors, etc.
            last_exc = e
            logger.warning("Network error calling %s (attempt=%d/%d): %s", url, attempt + 1, max_retries, str(e))
            if attempt < max_retries:
                _sleep_backoff(attempt)
                continue
            raise ToolHTTPError(error_type="network", message=str(e), url=url) from e
        
        except ToolHTTPError:
            # Already normalized
            raise
        
        except Exception as e:
            last_exc = e
            logger.error("Unexpected error calling %s (attempt=%d/%d): %s", url, attempt + 1, max_retries, str(e))
            raise ToolHTTPError(error_type="unexpected", message=str(e), url=url) from e
    
    # Should never reach here
    raise ToolHTTPError(
        error_type="unexpected",
        message=f"Request loop exhausted unexpectedly. Last exception: {last_exc!r}",
        url=url,
    )


def request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    data: Any | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> dict[str, Any]:
    """
    Same as request(), but parses response as JSON dict.
    Raises ToolHTTPError(error_type="parse") if JSON decoding fails.
    """
    resp = request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        json_body=json_body,
        data=data,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )
    try:
        return resp.json()
    except Exception as e:
        raise ToolHTTPError(
            error_type="parse",
            message=f"Failed to parse JSON from response: {e}",
            status_code=resp.status_code,
            url=url,
            response_text=_safe_text(resp),
        ) from e
