# ForenSight — Forensic Data Model Specification

## Entity Relational Overview

```
 [InvestigationCase] 1 ──── <many> [EvidenceRecord]
         │                                │
         │ 1                              │ 1
         │                                │
         ├──── <many> [SecurityEvent] <───┘ (optional origin)
         │
         └──── <many> [AuditRecord]
```

### 1. InvestigationCase
Represents an active or historical forensic incident inquiry.
- `id`: Integer (Primary Key, autoincrement)
- `case_number`: String (Unique, e.g. `FS-2026-0001`)
- `title`: String(255)
- `description`: Text
- `investigator_name`: String(100)
- `lead_analyst`: String(100)
- `status`: String (`OPEN`, `IN_PROGRESS`, `UNDER_REVIEW`, `CLOSED`, `ARCHIVED`)
- `priority`: String (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- `created_at`: DateTime (UTC)
- `updated_at`: DateTime (UTC)

### 2. EvidenceRecord
Represents a physical or digital artifact collected for analysis.
- `id`: Integer (Primary Key)
- `case_id`: Integer (Foreign Key -> investigation_cases.id, ondelete="CASCADE")
- `evidence_number`: String(50) (e.g. `EVD-001`)
- `source_filename`: String(255) (Original name upon acquisition)
- `stored_filename`: String(255) (Safe randomized/sanitized filename in vault)
- `file_path`: String(500) (Relative path inside storage vault)
- `file_size_bytes`: BigInteger
- `mime_type`: String(100)
- `sha256_hash`: String(64) (Cryptographic verification hash)
- `md5_hash`: String(32, nullable)
- `acquired_by`: String(100)
- `acquired_at`: DateTime (UTC)
- `chain_of_custody_notes`: Text
- `integrity_status`: String (`VERIFIED`, `PENDING`, `COMPROMISED`)
- `is_read_only`: Boolean (Default True)
- `created_at`: DateTime (UTC)
- `updated_at`: DateTime (UTC)

### 3. SecurityEvent
Represents an atomic security log entry or telemetry observation extracted from evidence or ingested logs.
- `id`: Integer (Primary Key)
- `case_id`: Integer (Foreign Key -> investigation_cases.id, ondelete="CASCADE")
- `evidence_id`: Integer (Foreign Key -> evidence_records.id, nullable, ondelete="SET NULL")
- `timestamp`: DateTime (UTC) (Event timestamp in normalized UTC)
- `event_type`: String(50) (`AUTHENTICATION`, `NETWORK_CONNECTION`, `PROCESS_EXECUTION`, `FILE_MODIFICATION`, `PRIVILEGE_ESCALATION`, `SUSPICIOUS_INDICATOR`)
- `severity`: String(20) (`INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- `source_ip`: String(45, nullable)
- `destination_ip`: String(45, nullable)
- `user_account`: String(100, nullable)
- `description`: Text
- `raw_data`: Text (Original log line or JSON payload)
- `indicator_tags`: Text (Comma-separated or serialized tags, e.g., `T1078,BruteForce`)
- `created_at`: DateTime (UTC)

### 4. AuditRecord
Application audit record of supported actions taken by users or system tasks. Records are not protected against direct database modification.
- `id`: Integer (Primary Key)
- `case_id`: Integer (Foreign Key -> investigation_cases.id, nullable, ondelete="SET NULL")
- `timestamp`: DateTime (UTC)
- `operator`: String(100)
- `action`: String(50) (e.g. `CASE_CREATED`, `EVIDENCE_INGESTED`, `HASH_VERIFIED`, `EVENT_FLAGGED`, `REPORT_GENERATED`)
- `target_type`: String(50) (`CASE`, `EVIDENCE`, `SECURITY_EVENT`, `SYSTEM`)
- `target_id`: String(100)
- `details`: Text
- `ip_address`: String(45, nullable)
- `action_hash`: String(64, nullable)

