import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# Known file signatures (magic bytes)
FILE_SIGNATURES = [
    {
        "name": "Windows Portable Executable (PE)",
        "magic": b"MZ",
        "mime": "application/x-dosexec",
        "category": "executable",
        "typical_extensions": [".exe", ".dll", ".sys", ".scr", ".cpl", ".ocx"],
    },
    {
        "name": "ELF Executable (Linux/Unix)",
        "magic": b"\x7fELF",
        "mime": "application/x-executable",
        "category": "executable",
        "typical_extensions": [".elf", ".so", ".bin", ""],
    },
    {
        "name": "Adobe PDF Document",
        "magic": b"%PDF",
        "mime": "application/pdf",
        "category": "document",
        "typical_extensions": [".pdf"],
    },
    {
        "name": "ZIP Archive / OpenXML Package",
        "magic": b"PK\x03\x04",
        "mime": "application/zip",
        "category": "archive",
        "typical_extensions": [".zip", ".docx", ".xlsx", ".pptx", ".jar", ".apk"],
    },
    {
        "name": "PNG Image",
        "magic": b"\x89PNG\r\n\x1a\n",
        "mime": "image/png",
        "category": "image",
        "typical_extensions": [".png"],
    },
    {
        "name": "JPEG Image",
        "magic": b"\xff\xd8\xff",
        "mime": "image/jpeg",
        "category": "image",
        "typical_extensions": [".jpg", ".jpeg"],
    },
    {
        "name": "GIF87a Image",
        "magic": b"GIF87a",
        "mime": "image/gif",
        "category": "image",
        "typical_extensions": [".gif"],
    },
    {
        "name": "GIF89a Image",
        "magic": b"GIF89a",
        "mime": "image/gif",
        "category": "image",
        "typical_extensions": [".gif"],
    },
    {
        "name": "GZIP Compressed Archive",
        "magic": b"\x1f\x8b",
        "mime": "application/gzip",
        "category": "archive",
        "typical_extensions": [".gz", ".tgz"],
    },
    {
        "name": "SQLite 3 Database",
        "magic": b"SQLite format 3\x00",
        "mime": "application/vnd.sqlite3",
        "category": "database",
        "typical_extensions": [".db", ".sqlite", ".sqlite3"],
    },
]

EXECUTABLE_EXTENSIONS = {
    ".exe", ".dll", ".sys", ".scr", ".bat", ".cmd", ".ps1", ".vbs",
    ".js", ".jse", ".wsf", ".wsh", ".hta", ".cpl", ".msi", ".jar",
    ".sh", ".bash", ".elf", ".bin", ".com",
}

DECEPTIVE_DOC_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".gif", ".txt", ".mp4", ".zip",
}


def detect_file_signature(file_path: Path) -> Optional[Dict[str, Any]]:
    """Inspects initial file bytes to identify magic file signature."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(32)
    except Exception:
        return None

    for sig in FILE_SIGNATURES:
        if header.startswith(sig["magic"]):
            return {
                "name": sig["name"],
                "mime": sig["mime"],
                "category": sig["category"],
                "typical_extensions": sig["typical_extensions"],
            }

    # Best-effort text heuristic
    try:
        header.decode("utf-8")
        return {
            "name": "ASCII / UTF-8 Plain Text",
            "mime": "text/plain",
            "category": "text",
            "typical_extensions": [".txt", ".log", ".csv", ".json", ".xml", ".ini", ".conf", ".example"],
        }
    except UnicodeDecodeError:
        return None


def inspect_evidence_metadata(
    vault_dir: Path,
    stored_filename: str,
    source_filename: str,
    acquired_at: datetime,
    original_sha256: str,
    md5_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract comprehensive forensic metadata and suspicious indicators.

    Distinguishes source acquisition metadata from physical vault storage timestamps.
    """
    file_path = (vault_dir / stored_filename).resolve()
    file_exists = file_path.exists() and file_path.is_file()

    # File extensions
    suffixes = Path(source_filename).suffixes
    full_ext = "".join(suffixes).lower()
    last_ext = Path(source_filename).suffix.lower()

    # MIME type detection (via Python standard library)
    guessed_mime, _ = mimetypes.guess_type(source_filename)
    if not guessed_mime:
        guessed_mime = "application/octet-stream"

    # Filesystem stats
    stat_info = None
    file_size = 0
    vault_mtime_utc = None
    vault_ctime_utc = None

    if file_exists:
        try:
            stat_info = file_path.stat()
            file_size = stat_info.st_size
            vault_mtime_utc = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
            vault_ctime_utc = datetime.fromtimestamp(stat_info.st_ctime, tz=timezone.utc)
        except Exception:
            pass

    # Signature detection
    signature = detect_file_signature(file_path) if file_exists else None

    # Investigative Indicators (Rule-based heuristics)
    indicators: List[Dict[str, str]] = []

    # 1. Suspicious Double Extension (e.g. document.pdf.exe)
    if len(suffixes) >= 2:
        penultimate = suffixes[-2].lower()
        ultimate = suffixes[-1].lower()
        if penultimate in DECEPTIVE_DOC_EXTENSIONS and ultimate in EXECUTABLE_EXTENSIONS:
            indicators.append({
                "rule": "SUSPICIOUS_DOUBLE_EXTENSION",
                "severity": "HIGH",
                "description": f"File uses deceptive compound extension ('{penultimate}{ultimate}'). Commonly used to disguise executable payloads as documents.",
            })

    # 2. Selected Executable File Type Indicator
    if last_ext in EXECUTABLE_EXTENSIONS or (signature and signature.get("category") == "executable"):
        indicators.append({
            "rule": "EXECUTABLE_PAYLOAD_TYPE",
            "severity": "MEDIUM",
            "description": f"File type or signature corresponds to an executable binary or script ({last_ext or signature.get('name')}).",
        })

    # 3. Extension / Signature Mismatch
    if signature and signature.get("typical_extensions"):
        valid_exts = [e.lower() for e in signature["typical_extensions"] if e]
        if valid_exts and last_ext not in valid_exts:
            # Check if text file with script or code extension
            is_text_doc = signature["mime"].startswith("text/") and last_ext in [".log", ".txt", ".csv", ".json", ".py", ".md", ".example"]
            if not is_text_doc:
                indicators.append({
                    "rule": "SIGNATURE_EXTENSION_MISMATCH",
                    "severity": "HIGH",
                    "description": f"File magic signature indicates '{signature['name']}' ({signature['mime']}), but extension is declared as '{last_ext}'.",
                })

    return {
        "source_metadata": {
            "source_filename": source_filename,
            "file_extension": last_ext,
            "full_extensions": full_ext,
            "declared_mime_type": guessed_mime,
            "acquisition_timestamp_utc": acquired_at.isoformat(),
            "sha256_hash": original_sha256,
            "md5_hash": md5_hash,
        },
        "vault_storage_metadata": {
            "stored_filename": stored_filename,
            "file_exists": file_exists,
            "actual_size_bytes": file_size,
            "vault_filesystem_mtime_utc": vault_mtime_utc.isoformat() if vault_mtime_utc else None,
            "vault_filesystem_ctime_utc": vault_ctime_utc.isoformat() if vault_ctime_utc else None,
        },
        "signature_analysis": {
            "signature_detected": signature is not None,
            "signature_name": signature["name"] if signature else "Unknown / Raw Binary",
            "detected_mime_type": signature["mime"] if signature else guessed_mime,
            "category": signature["category"] if signature else "unknown",
        },
        "investigative_indicators": indicators,
    }
