# ForenSight — Technical Architecture & Design Document

## 1. System Vision

ForenSight is built to solve common challenges in lightweight digital investigations:
- Recording evidence acquisition and investigation actions in a local workbench.
- Correlating heterogeneous artifacts (network logs, system events, disk files) across unified timelines.
- Storing uploaded copies and checking their hashes against recorded baselines.

## 2. High-Level Architecture

```
+-------------------------------------------------------------+
|                     ForenSight Web Client                   |
|   (React 18, React Router v6, Tailwind CSS, Lucide Icons)   |
|   - Real-time Health & Integrity Telemetry                   |
|   - Case Workspace & Forensic Investigation Shell           |
+------------------------------+------------------------------+
                               |
                               | REST / JSON (dev CORS)
                               v
+-------------------------------------------------------------+
|                     FastAPI Backend                         |
|   - Versioned API: /api/v1 (cases, evidence, events, audit) |
|   - Diagnostics API: /api/health                            |
|   - Pydantic v2 Models & UTC Serialization                  |
|   - Evidence Storage Manager & SHA-256 Hashing Engine       |
+------------------------------+------------------------------+
                               |
               +---------------+---------------+
               |                               |
               v                               v
    +--------------------+           +--------------------+
    | SQLite  |           | Evidence Vault     |
    | SQLAlchemy 2.0 ORM |           | (Isolated FS)      |
    | - Cases            |           | - Stored Copies    |
    | - Evidence Records |           | - Read-only flags  |
    | - Security Events  |           | - Hash verifiers   |
    | - Audit Log        |           +--------------------+
    +--------------------+
```

## 3. Data Integrity & Chain of Custody

1. **Evidence Ingestion**: When an artifact is provided, the backend computes its SHA-256 immediately upon ingestion, generates an evidence ID, and stores the copy in a non-web-accessible vault directory.
2. **Audit Logging**: Supported investigation operations generate an `AuditRecord` referencing the operator and case context; not every read is audited.
3. **UTC Everywhere**: All database columns and API inputs/outputs enforce UTC timezone stamps.

## Security limits

Read-only file attributes are best effort. Local database access can modify audit records and recorded hash baselines. This application does not provide immutable storage, authenticated operator identities, or cryptographic non-repudiation. See README.md for deployment limits.

