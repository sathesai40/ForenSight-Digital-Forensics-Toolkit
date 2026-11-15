import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any


def calculate_file_sha256(file_path: Path) -> str:
    """Calculate SHA-256 digest of an on-disk file using streaming chunks."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(64 * 1024):
            sha256.update(chunk)
    return sha256.hexdigest().lower()


def verify_evidence_integrity(
    vault_dir: Path,
    stored_filename: str,
    original_sha256: str,
) -> Dict[str, Any]:
    """Verify stored evidence file against its recorded acquisition SHA-256 hash.

    Returns a structured verification result with status: MATCH, MISMATCH, or ERROR.
    """
    now_utc = datetime.now(timezone.utc)
    file_path = (vault_dir / stored_filename).resolve()

    # Verify path containment inside vault_dir
    if not file_path.is_relative_to(vault_dir.resolve()):
        return {
            "status": "ERROR",
            "expected_sha256": original_sha256.lower(),
            "calculated_sha256": None,
            "verified_at": now_utc,
            "detail": "Path traversal or invalid file location detected.",
            "file_exists": False,
        }

    if not file_path.exists() or not file_path.is_file():
        return {
            "status": "ERROR",
            "expected_sha256": original_sha256.lower(),
            "calculated_sha256": None,
            "verified_at": now_utc,
            "detail": f"Evidence artifact file '{stored_filename}' was not found in the storage vault.",
            "file_exists": False,
        }

    try:
        calculated_hash = calculate_file_sha256(file_path)
    except Exception as e:
        return {
            "status": "ERROR",
            "expected_sha256": original_sha256.lower(),
            "calculated_sha256": None,
            "verified_at": now_utc,
            "detail": f"Failed to read evidence bytes: {str(e)}",
            "file_exists": True,
        }

    expected = original_sha256.lower().strip()
    if calculated_hash == expected:
        return {
            "status": "MATCH",
            "expected_sha256": expected,
            "calculated_sha256": calculated_hash,
            "verified_at": now_utc,
            "detail": "Cryptographic SHA-256 integrity check verified: byte-level match confirmed.",
            "file_exists": True,
        }
    else:
        return {
            "status": "MISMATCH",
            "expected_sha256": expected,
            "calculated_sha256": calculated_hash,
            "verified_at": now_utc,
            "detail": "Cryptographic integrity compromised! Calculated hash differs from original acquisition hash.",
            "file_exists": True,
        }
