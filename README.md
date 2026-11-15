# ForenSight - Digital Forensics Investigation Toolkit

A local digital forensics workbench for managing cases, examining uploaded evidence, checking file integrity, correlating security logs, and exporting investigation reports.

## Features

- Case creation, status and priority updates, and dashboard statistics.
- Evidence upload with randomized storage names, filename sanitization, a configurable size limit (25 MB by default), SHA-256 and MD5 hashes, and read-only storage attributes where supported.
- SHA-256 re-verification with MATCH, MISMATCH, and ERROR results.
- File metadata, magic-byte inspection, and heuristic indicators for executable content, extension mismatches, and suspicious double extensions.
- Authentication/syslog and CSV log ingestion, repeated-import deduplication, repeated failed-login detection, account targeting, and failure-then-success sequence detection.
- Case timelines combining evidence acquisition, security events, integrity checks, and audit actions.
- ReportLab PDF case reports and an audit trail for supported investigation operations.

## Architecture and stack

The React client calls a FastAPI REST API. SQLAlchemy persists cases, evidence metadata, security events, and audit records in SQLite. Uploaded file copies live in a separate filesystem vault.

| Directory | Purpose |
| --- | --- |
| `backend/app/api/v1/` | Cases, evidence, log analysis, timeline, dashboard, audit, reports, health |
| `backend/app/forensics/` | Vault acquisition, verification, metadata, log parsing, PDF generation |
| `backend/app/models/`, `schemas/` | SQLAlchemy models and Pydantic schemas |
| `backend/tests/` | Automated API, model, workflow, and security regression tests |
| `frontend/src/` | React 18, React Router 6, Tailwind CSS 3, Lucide icons |
| `docs/` | Architecture and data model notes |
| `sample_data/` | Synthetic demonstration payload and authentication log |

Backend dependencies include FastAPI, Uvicorn, SQLAlchemy 2, Pydantic 2, and ReportLab. The frontend uses Vite 6. See the dependency manifests for declared versions; backend requirements use minimum versions rather than a lockfile.

## Install and run (PowerShell)

Verified locally with Python 3.13.14, Node.js 24.16.0, and Vite 6.4.6. Other runtime versions have not been verified in this review.

From the project root:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```

The existing Vite development proxy targets port **8002**. The backend command above matches it. Backend health: `http://127.0.0.1:8002/api/health`; API documentation: `http://127.0.0.1:8002/docs`.

In another terminal, from the project root:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. The client uses `/api` by default. To use another backend port, create an ignored `frontend/.env.local` with `VITE_API_BASE_URL=http://127.0.0.1:8000/api` and launch Uvicorn on that port. Vite reads environment files from `frontend/`; the root environment example is a reference, not automatically shared configuration.

Backend configuration is loaded from `backend/.env` when launched from `backend/`. Keep the default loopback CORS origins. Database and vault paths are relative to the backend working directory by default. Never replace an existing database or vault when following setup instructions; copy the environment example only for a new installation.

## Verification

On November 15, 2026, the existing automated backend suite completed with **26 passing tests**, and `npm run build` completed successfully. Tests cover case operations, evidence upload and hash verification, metadata, log parsing and deduplication, timeline aggregation, dashboard metrics, PDF output, filename traversal sanitization, oversized evidence rejection, and tampered/missing evidence handling.

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -p no:cacheprovider
cd ..\frontend
npm run build
```

The automated suite uses an in-memory database and synthetic evidence. `backend/tests/verify_phase4_live.py` is a separate manual script that writes to a running service and includes hardcoded local vault paths and synthetic-file tampering/deletion checks. Do not run it against an existing investigation environment. It was not executed for this publication review. A production build does not establish browser workflow correctness; no new browser verification was performed.

## Demonstration data and screenshots

`sample_data/sample_evidence.bin` is a plain-text synthetic payload. `sample_data/raw_logs/sample_auth.log.example` uses documentation IP addresses and fictional log entries. No screenshots are included in the project; use synthetic cases if adding screenshots later.

## Security and limitations

- Intended for a trusted, local, single-examiner workstation. There is no authentication or role-based access control. Bind to loopback and do not expose the service publicly. CORS is not an authentication boundary.
- Read-only file attributes are best effort and can be changed by an operating-system user. The vault is not immutable storage, and audit records are not cryptographically tamper-proof or independently authenticated. SHA-256 detects changes relative to a recorded baseline; it does not establish provenance or legal admissibility.
- Log detections and file-signature checks are limited investigative heuristics. They do not replace a full forensic suite, malware sandbox, or expert review. MD5 is included as metadata; use SHA-256 for integrity checks.
- Log uploads are read into memory; large or untrusted inputs require additional resource controls. No production deployment hardening or dependency-vulnerability certification is claimed.
- SQLite and local filesystem storage require an independent backup and access-control strategy. Backend dependencies are not pinned to exact versions.
- Private configuration, databases, evidence vaults, uploaded files, raw `.log` files, PDF reports, dependency directories, and generated builds are ignored by Git. Review every proposed commit; ignore rules do not sanitize arbitrary files or previously committed content.

See [architecture](docs/architecture.md) and [data model](docs/forensics-data-model.md) for implementation notes.

## License

No LICENSE file has been supplied. The previous README mentioned MIT, but an explicit license grant and copyright notice need to be added by the owner before describing this project as MIT-licensed.
