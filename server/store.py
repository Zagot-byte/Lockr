#!/usr/bin/env python3
"""
store.py — Git-architecture content-addressable secret store.

.vault/ layout mirrors git's object model:
  objects/{aa}/{bb...}   encrypted blobs, named by SHA-256 of ciphertext
  refs/heads/{env}/{ns}/{key}  pointer files containing object hash
  HEAD                   current environment name
  vault.toml             config (KEK public key, settings)
"""

import os
import json
import shutil
from pathlib import Path
from typing import Optional, List

from .crypto import (
    EncryptedBlob,
    encrypt,
    decrypt,
    content_hash,
)

DEFAULT_VAULT_DIR = Path(".vault")


class VaultStore:
    """
    Git-style content-addressable secret store.

    All reads/writes go through content-addressed objects.
    Refs (pointers) map secret paths to object hashes.
    Old versions are never deleted — just dereferenced.
    """

    def __init__(self, vault_dir: Path = DEFAULT_VAULT_DIR):
        self.root     = vault_dir
        self.objects  = vault_dir / "objects"
        self.refs     = vault_dir / "refs" / "heads"
        self.head     = vault_dir / "HEAD"
        self.audit_log = vault_dir / "audit.log"
        self.config   = vault_dir / "vault.toml"

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def init(self, default_env: str = "prod") -> None:
        """
        Create a fresh .vault/ directory structure.
        Equivalent to `git init`.
        """
        if self.root.exists():
            raise FileExistsError(f"{self.root} already exists. Already initialised.")

        self.objects.mkdir(parents=True)
        (self.refs).mkdir(parents=True)
        (self.refs / default_env).mkdir(parents=True)
        self.head.write_text(default_env)

        self.config.write_text(
            f'[vault]\nversion = "1"\ndefault_env = "{default_env}"\n'
            f'kek_algorithm = "FrodoKEM-1344-SHAKE"\n'
        )

        self.audit_log.touch()

    def is_initialised(self) -> bool:
        return self.root.exists() and self.head.exists()

    # ------------------------------------------------------------------
    # Environment (HEAD / branches)
    # ------------------------------------------------------------------

    def current_env(self) -> str:
        """Read HEAD — current active environment."""
        return self.head.read_text().strip()

    def checkout(self, env: str) -> None:
        """Switch environment. Creates branch dir if new."""
        (self.refs / env).mkdir(parents=True, exist_ok=True)
        self.head.write_text(env)

    def list_envs(self) -> List[str]:
        return [p.name for p in self.refs.iterdir() if p.is_dir()]

    # ------------------------------------------------------------------
    # Object store — content-addressable blobs
    # ------------------------------------------------------------------

    def _object_path(self, hash_hex: str) -> Path:
        """Shard by first 2 chars — same as git."""
        return self.objects / hash_hex[:2] / hash_hex[2:]

    def _write_object(self, blob: EncryptedBlob) -> str:
        """
        Write encrypted blob to objects store.
        Returns the content hash (object name).
        Content-addressed: writing the same secret twice = same hash.
        """
        raw      = blob.to_bytes()
        hash_hex = content_hash(raw)
        obj_path = self._object_path(hash_hex)

        if not obj_path.exists():
            obj_path.parent.mkdir(parents=True, exist_ok=True)
            obj_path.write_bytes(raw)

        return hash_hex

    def _read_object(self, hash_hex: str) -> EncryptedBlob:
        """Read and deserialize a blob from the object store."""
        obj_path = self._object_path(hash_hex)
        if not obj_path.exists():
            raise FileNotFoundError(f"Object {hash_hex} not found in store.")
        return EncryptedBlob.from_bytes(obj_path.read_bytes())

    # ------------------------------------------------------------------
    # Refs — path → hash pointers
    # ------------------------------------------------------------------

    def _ref_path(self, env: str, namespace: str, key: str) -> Path:
        """Map (env, namespace, key) → ref file path."""
        return self.refs / env / namespace / key

    def _write_ref(self, env: str, namespace: str, key: str, hash_hex: str) -> None:
        ref = self._ref_path(env, namespace, key)
        ref.parent.mkdir(parents=True, exist_ok=True)
        ref.write_text(hash_hex)

    def _read_ref(self, env: str, namespace: str, key: str) -> Optional[str]:
        ref = self._ref_path(env, namespace, key)
        if not ref.exists():
            return None
        return ref.read_text().strip()

    def _delete_ref(self, env: str, namespace: str, key: str) -> bool:
        ref = self._ref_path(env, namespace, key)
        if not ref.exists():
            return False
        ref.unlink()
        return True

    # ------------------------------------------------------------------
    # Public CRUD — secrets
    # ------------------------------------------------------------------

    def set(self, path: str, value: bytes, env: Optional[str] = None) -> str:
        """
        Write a secret.

        Args:
            path  : "namespace/key" e.g. "myapp/db_password"
            value : raw secret bytes
            env   : environment (defaults to HEAD)

        Returns:
            Object hash of the written blob
        """
        env = env or self.current_env()
        ns, key = self._split_path(path)

        blob     = encrypt(value, f"{env}/{path}")
        hash_hex = self._write_object(blob)
        self._write_ref(env, ns, key, hash_hex)

        return hash_hex

    def get(self, path: str, env: Optional[str] = None) -> bytes:
        """
        Read a secret.

        Args:
            path : "namespace/key"
            env  : environment (defaults to HEAD)

        Returns:
            Raw secret bytes

        Raises:
            KeyError if secret doesn't exist
        """
        env = env or self.current_env()
        ns, key = self._split_path(path)

        hash_hex = self._read_ref(env, ns, key)
        if hash_hex is None:
            raise KeyError(f"Secret '{env}/{path}' not found.")

        blob = self._read_object(hash_hex)
        return decrypt(blob)

    def delete(self, path: str, env: Optional[str] = None) -> bool:
        """
        Delete a secret ref (object stays in store — git-style).
        Returns True if deleted, False if didn't exist.
        """
        env = env or self.current_env()
        ns, key = self._split_path(path)
        return self._delete_ref(env, ns, key)

    def list(self, namespace: str, env: Optional[str] = None) -> List[str]:
        """List all secret keys in a namespace."""
        env = env or self.current_env()
        ns_path = self.refs / env / namespace
        if not ns_path.exists():
            return []
        return [f.name for f in ns_path.iterdir() if f.is_file()]

    def exists(self, path: str, env: Optional[str] = None) -> bool:
        env = env or self.current_env()
        ns, key = self._split_path(path)
        return self._read_ref(env, ns, key) is not None

    # ------------------------------------------------------------------
    # History — old object hashes never deleted
    # ------------------------------------------------------------------

    def history(self, path: str, env: Optional[str] = None) -> List[str]:
        """
        Return all object hashes ever written for a path.
        Walks objects/ dir — brute force for MVP.
        TODO: replace with a proper reflog in v2.
        """
        env = env or self.current_env()
        aad = f"{env}/{path}".encode()
        found = []

        for obj_file in self.objects.glob("*/*"):
            try:
                blob = EncryptedBlob.from_bytes(obj_file.read_bytes())
                if blob.aad == aad:
                    found.append(obj_file.parent.name + obj_file.name)
            except Exception:
                continue

        return found

    # ------------------------------------------------------------------
    # Branch ops — promote secrets between envs
    # ------------------------------------------------------------------

    def merge(self, src_env: str, dst_env: str) -> int:
        """
        Copy all refs from src_env → dst_env.
        Objects already exist — just updates pointers.
        Returns count of merged refs.
        """
        src_root = self.refs / src_env
        if not src_root.exists():
            raise FileNotFoundError(f"Environment '{src_env}' not found.")

        count = 0
        for ref_file in src_root.glob("**/*"):
            if not ref_file.is_file():
                continue

            rel       = ref_file.relative_to(src_root)
            parts     = rel.parts
            if len(parts) < 2:
                continue

            namespace = parts[0]
            key       = "/".join(parts[1:])
            hash_hex  = ref_file.read_text().strip()
            self._write_ref(dst_env, namespace, key, hash_hex)
            count += 1

        return count

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _split_path(path: str):
        """Split "namespace/key" → ("namespace", "key"). Validates format."""
        parts = path.strip("/").split("/", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(
                f"Invalid secret path: '{path}'. Expected 'namespace/key'."
            )
        return parts[0], parts[1]
