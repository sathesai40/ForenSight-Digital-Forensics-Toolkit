import os
import re
import stat
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Dict, Any, Tuple


def sanitize_filename(filename: str) -> str:
    """Sanitize original filename to prevent path traversal and unsafe characters.

    Strips directory separators, null bytes, relative traversal patterns ('..'),
    and non-printable characters.
    """
    if not filename:
        return "evidence_artifact.bin"

    # Remove path components (both forward and backward slashes)
    base = os.path.basename(filename.replace("\\", "/"))
    # Remove null bytes and control characters
    clean = re.sub(r"[\x00-\x1f\x7f]", "", base)
    # Remove traversal sequences
    clean = clean.replace("..", "").strip(". ")

    # Whitelist characters (alphanumeric, dot, underscore, dash, space)
    clean = re.sub(r"[^\w\.\-\s]", "_", clean)

    if not clean or clean.startswith("."):
        return f"evidence_{uuid.uuid4().hex[:8]}.bin"

    return clean[:200]  # Cap length for filesystem safety


def acquire_evidence_stream(
    stream: BinaryIO,
    original_filename: str,
    vault_dir: Path,
    max_size_bytes: int,
) -> Dict[str, Any]:
    """Streams uploaded evidence into the vault while calculating SHA-256 and MD5.

    Enforces size boundaries, prevents path traversal, sets read-only permissions,
    and cleans up on failure.
    """
    vault_dir.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_filename(original_filename)
    unique_prefix = uuid.uuid4().hex
    stored_filename = f"evd_{unique_prefix}_{safe_name}"
    target_path = (vault_dir / stored_filename).resolve()

    # Double check that resolved path is inside vault_dir
    if not target_path.is_relative_to(vault_dir.resolve()):
        raise ValueError("Invalid target path: directory traversal detected.")

    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    total_bytes = 0
    chunk_size = 64 * 1024  # 64 KB chunks

    try:
        with open(target_path, "wb") as out_file:
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_size_bytes:
                    raise ValueError(
                        f"Evidence file size exceeds maximum limit of {max_size_bytes // (1024 * 1024)} MB."
                    )
                sha256.update(chunk)
                md5.update(chunk)
                out_file.write(chunk)

        # Enforce read-only permission on stored evidence file (forensic preservation)
        try:
            target_path.chmod(stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
        except Exception:
            # Fallback if chmod fails on some restricted windows setups
            pass

        acquired_at = datetime.now(timezone.utc)

        return {
            "source_filename": safe_name,
            "stored_filename": stored_filename,
            "file_path": f"vault/{stored_filename}",  # Safe relative path, never absolute
            "absolute_path": target_path,
            "file_size_bytes": total_bytes,
            "sha256_hash": sha256.hexdigest().lower(),
            "md5_hash": md5.hexdigest().lower(),
            "acquired_at": acquired_at,
        }

    except Exception:
        # Failure cleanup: never leave orphaned or partial files in the vault
        if target_path.exists():
            try:
                # Remove read-only attribute if set, then delete
                target_path.chmod(stat.S_IWRITE)
                target_path.unlink(missing_ok=True)
            except Exception:
                pass
        raise
