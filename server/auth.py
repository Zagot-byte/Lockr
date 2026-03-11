#!/usr/bin/env python3
"""
auth.py — Token CRUD + scope enforcement.

Tokens are scoped to namespaces via glob patterns.
Stored in .vault/tokens/ (never in the secret object store).
"""

import os
import json
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from fnmatch import fnmatch

DEFAULT_TOKEN_DIR = Path(".vault/tokens")

TOKEN_PREFIX = "tk_"


class TokenExpiredError(Exception):
    pass


class TokenNotFoundError(Exception):
    pass


class ScopeViolationError(Exception):
    pass


def _parse_ttl(ttl: str) -> timedelta:
    """Parse TTL string: '24h', '7d', '30m', '1y'."""
    unit  = ttl[-1].lower()
    value = int(ttl[:-1])
    return {
        "m": timedelta(minutes=value),
        "h": timedelta(hours=value),
        "d": timedelta(days=value),
        "y": timedelta(days=value * 365),
    }.get(unit, timedelta(hours=value))


class AuthStore:
    """
    Token lifecycle management.

    Token file format (.vault/tokens/{hash}.json):
    {
      "id":        "tk_abc123...",
      "label":     "john-staging",
      "scopes":    ["staging/*", "myapp/api_*"],
      "created":   "2025-01-01T00:00:00Z",
      "expires":   "2025-01-02T00:00:00Z",   // null = never
      "revoked":   false
    }

    Token IDs stored hashed on disk — raw token only returned on creation.
    """

    def __init__(self, token_dir: Path = DEFAULT_TOKEN_DIR):
        self.dir = token_dir
        self.dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Token CRUD
    # ------------------------------------------------------------------

    def create(
        self,
        scopes: List[str],
        ttl:    Optional[str] = None,
        label:  Optional[str] = None,
    ) -> str:
        """
        Create a new token.

        Args:
            scopes : list of namespace glob patterns e.g. ["staging/*", "myapp/api_*"]
            ttl    : TTL string e.g. "24h", "7d". None = never expires.
            label  : human-readable label e.g. "john-staging"

        Returns:
            Raw token string (only returned once — store securely).
        """
        raw_token = TOKEN_PREFIX + secrets.token_urlsafe(32)
        token_id  = self._hash_token(raw_token)

        now     = datetime.now(timezone.utc)
        expires = (now + _parse_ttl(ttl)).isoformat() if ttl else None

        record = {
            "id":      token_id,
            "label":   label or token_id[:12],
            "scopes":  scopes,
            "created": now.isoformat(),
            "expires": expires,
            "revoked": False,
        }

        self._write(token_id, record)
        return raw_token

    def revoke(self, raw_token_or_id: str) -> bool:
        """
        Revoke a token by raw token string or token ID.
        Returns True if revoked, False if not found.
        """
        token_id = (
            self._hash_token(raw_token_or_id)
            if raw_token_or_id.startswith(TOKEN_PREFIX)
            else raw_token_or_id
        )

        record = self._read(token_id)
        if record is None:
            return False

        record["revoked"] = True
        self._write(token_id, record)
        return True

    def list(self) -> List[Dict]:
        """List all tokens (metadata only — no raw values)."""
        tokens = []
        for f in self.dir.glob("*.json"):
            try:
                record = json.loads(f.read_text())
                # Strip internal hash ID from listing
                tokens.append({
                    "label":   record["label"],
                    "scopes":  record["scopes"],
                    "created": record["created"],
                    "expires": record["expires"],
                    "revoked": record["revoked"],
                    "active":  self._is_active(record),
                })
            except Exception:
                continue
        return tokens

    # ------------------------------------------------------------------
    # Auth / scope enforcement
    # ------------------------------------------------------------------

    def validate(self, raw_token: str, path: str, action: str) -> Dict:
        """
        Validate a token and check it has scope for (path, action).

        Args:
            raw_token : raw token string from request header
            path      : secret path e.g. "prod/db_password"
            action    : "read" | "write" | "delete" | "list"

        Returns:
            Token record if valid and scoped.

        Raises:
            TokenNotFoundError, TokenExpiredError, ScopeViolationError
        """
        token_id = self._hash_token(raw_token)
        record   = self._read(token_id)

        if record is None:
            raise TokenNotFoundError("Invalid token.")

        if record["revoked"]:
            raise TokenExpiredError("Token has been revoked.")

        if not self._is_active(record):
            raise TokenExpiredError("Token has expired.")

        if not self._has_scope(record["scopes"], path):
            raise ScopeViolationError(
                f"Token not scoped for '{path}'. Scopes: {record['scopes']}"
            )

        return record

    def validate_admin(self, raw_token: str) -> Dict:
        """
        Validate an admin token (scope = "*").
        Used for audit log access, compliance reports, token management.
        """
        token_id = self._hash_token(raw_token)
        record   = self._read(token_id)

        if record is None:
            raise TokenNotFoundError("Invalid token.")

        if record["revoked"]:
            raise TokenExpiredError("Token revoked.")

        if not self._is_active(record):
            raise TokenExpiredError("Token expired.")

        if "*" not in record["scopes"]:
            raise ScopeViolationError("Admin scope required.")

        return record

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_token(raw: str) -> str:
        """Hash raw token for on-disk storage. One-way."""
        return hashlib.sha256(raw.encode()).hexdigest()

    def _token_path(self, token_id: str) -> Path:
        return self.dir / f"{token_id}.json"

    def _write(self, token_id: str, record: Dict) -> None:
        self._token_path(token_id).write_text(
            json.dumps(record, indent=2)
        )

    def _read(self, token_id: str) -> Optional[Dict]:
        path = self._token_path(token_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except Exception:
            return None

    @staticmethod
    def _is_active(record: Dict) -> bool:
        if record.get("revoked"):
            return False
        expires = record.get("expires")
        if expires is None:
            return True
        return datetime.now(timezone.utc) < datetime.fromisoformat(expires)

    @staticmethod
    def _has_scope(scopes: List[str], path: str) -> bool:
        """Check if any scope glob matches the requested path."""
        return any(fnmatch(path, scope) for scope in scopes)
