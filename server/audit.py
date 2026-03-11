#!/usr/bin/env python3
"""
audit.py — Hash-chained, tamper-evident audit log.

Each entry hashes the previous entry's hash.
Modifying any entry breaks the entire chain — satisfies SOC-2 CC7.2.

Format: one JSON object per line (JSONL).
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

DEFAULT_LOG = Path(".vault/audit.log")


class AuditLog:
    """
    Append-only, hash-chained audit log.

    Chain integrity: entry[n].hash = SHA256(entry[n].prev_hash + entry[n].body)
    Verifiable with `verify_chain()` — run before any compliance report.
    """

    GENESIS_HASH = "0" * 64  # Sentinel for first entry

    def __init__(self, log_path: Path = DEFAULT_LOG):
        self.path = log_path

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def append(
        self,
        actor:     str,
        action:    str,
        target:    str,
        result:    str,
        metadata:  Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Append a new audit entry.

        Args:
            actor    : token ID or "system"
            action   : e.g. "secret_read", "token_create", "key_rotate"
            target   : secret path, namespace, or token ID
            result   : "success" | "denied" | "error"
            metadata : optional extra context (never contains secret values)

        Returns:
            Hash of the new entry
        """
        prev_hash = self._last_hash()

        body = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor":     actor,
            "action":    action,
            "target":    target,
            "result":    result,
            "prev_hash": prev_hash,
        }

        if metadata:
            body["metadata"] = metadata

        # Hash = SHA256(prev_hash + canonical JSON body)
        body_str  = json.dumps(body, sort_keys=True, separators=(",", ":"))
        entry_hash = hashlib.sha256(
            (prev_hash + body_str).encode()
        ).hexdigest()

        body["hash"] = entry_hash

        with open(self.path, "a") as f:
            f.write(json.dumps(body, separators=(",", ":")) + "\n")

        return entry_hash

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def tail(self, n: int = 50) -> List[Dict]:
        """Return the last n entries."""
        return self._all_entries()[-n:]

    def query(
        self,
        namespace:  Optional[str] = None,
        actor:      Optional[str] = None,
        action:     Optional[str] = None,
        since_iso:  Optional[str] = None,
        limit:      int = 200,
    ) -> List[Dict]:
        """
        Filter audit entries.

        Args:
            namespace : filter by target prefix
            actor     : filter by token/actor ID
            action    : filter by action type
            since_iso : ISO-8601 timestamp — only entries after this
            limit     : max results

        Returns:
            Matching entries, newest first
        """
        entries = self._all_entries()

        if since_iso:
            entries = [e for e in entries if e["timestamp"] >= since_iso]

        if namespace:
            entries = [e for e in entries if e["target"].startswith(namespace)]

        if actor:
            entries = [e for e in entries if e["actor"] == actor]

        if action:
            entries = [e for e in entries if e["action"] == action]

        return list(reversed(entries))[:limit]

    def detect_anomalies(
        self,
        since_iso: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> List[Dict]:
        """
        Basic anomaly detection heuristics.

        Flags:
          - >10 reads by same actor within 1 minute
          - Any "denied" result
          - Reads outside business hours (00:00–06:00 UTC)
          - Bulk reads (>20 unique secrets in one session)
        """
        entries = self.query(namespace=namespace, since_iso=since_iso, limit=1000)
        anomalies = []

        # Denied access
        denied = [e for e in entries if e["result"] == "denied"]
        for e in denied:
            anomalies.append({**e, "anomaly": "access_denied"})

        # Off-hours reads (00:00–06:00 UTC)
        for e in entries:
            hour = int(e["timestamp"][11:13])
            if e["action"] == "secret_read" and 0 <= hour < 6:
                anomalies.append({**e, "anomaly": "off_hours_read"})

        # High-frequency reads per actor
        from collections import Counter
        actor_counts: Counter = Counter()
        for e in entries:
            if e["action"] == "secret_read":
                actor_counts[e["actor"]] += 1

        for actor, count in actor_counts.items():
            if count > 20:
                anomalies.append({
                    "anomaly": "high_volume_reads",
                    "actor":   actor,
                    "count":   count,
                })

        return anomalies

    # ------------------------------------------------------------------
    # Verify
    # ------------------------------------------------------------------

    def verify_chain(self) -> bool:
        """
        Walk entire log and verify hash chain integrity.

        Returns:
            True if chain is intact, False if tampered.
        """
        entries = self._all_entries()
        if not entries:
            return True

        prev_hash = self.GENESIS_HASH

        for entry in entries:
            stored_hash = entry.pop("hash", None)
            body_str = json.dumps(entry, sort_keys=True, separators=(",", ":"))
            expected  = hashlib.sha256(
                (prev_hash + body_str).encode()
            ).hexdigest()

            if expected != stored_hash:
                return False

            entry["hash"] = stored_hash  # Restore
            prev_hash = stored_hash

        return True

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _all_entries(self) -> List[Dict]:
        if not self.path.exists():
            return []

        entries = []
        for line in self.path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return entries

    def _last_hash(self) -> str:
        entries = self._all_entries()
        if not entries:
            return self.GENESIS_HASH
        return entries[-1].get("hash", self.GENESIS_HASH)
