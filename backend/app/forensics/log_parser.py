import csv
import io
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional


def parse_timestamp_utc(time_str: str) -> datetime:
    """Parse various timestamp strings and normalize strictly to timezone-aware UTC."""
    clean = time_str.strip()

    # ISO 8601 with Z or offset
    if clean.endswith("Z"):
        clean_no_z = clean[:-1]
        try:
            dt = datetime.fromisoformat(clean_no_z)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    try:
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass

    # Common forensic log formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
        "%d/%b/%Y:%H:%M:%S",
        "%b %d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(clean, fmt)
            if dt.year == 1900:
                dt = dt.replace(year=datetime.now(timezone.utc).year)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return datetime.now(timezone.utc)


def parse_auth_syslog_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse single auth/syslog line into normalized security event fields."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    # Match ISO prefix or Syslog month-day prefix
    iso_prefix = r"^(\d{4}-\d{2}-\d{2}T[\d:\.]+Z?|\w{3}\s+\d+\s+[\d:]+)\s+([\w\.\-]+)\s+([\w\[\]\d]+):\s+(.*)$"
    match = re.match(iso_prefix, stripped)

    timestamp_raw = ""
    host = ""
    service = ""
    message = stripped

    if match:
        timestamp_raw, host, service, message = match.groups()
    else:
        parts = stripped.split(" ", 3)
        if len(parts) >= 4:
            timestamp_raw = parts[0]
            message = " ".join(parts[1:])

    dt_utc = parse_timestamp_utc(timestamp_raw) if timestamp_raw else datetime.now(timezone.utc)

    # Defaults
    event_type = "SYSTEM"
    severity = "INFO"
    source_ip = None
    destination_ip = None
    user_account = None
    indicator_tags = []

    # 1. Failed authentication attempt
    # e.g.: "Failed password for invalid user root from 198.51.100.42 port 54312 ssh2"
    # or:   "Failed password for user svc_admin from 203.0.113.88 port 41200 ssh2"
    # or:   "Failed password for admin from 10.0.0.1 port 22"
    failed_match = re.search(
        r"Failed (?:password|publickey) for (?:(?:invalid\s+)?user\s+)?(\w+) from ([\d\.]+) port (\d+)",
        message,
        re.IGNORECASE,
    )
    if failed_match:
        user_account = failed_match.group(1)
        source_ip = failed_match.group(2)
        event_type = "AUTHENTICATION"
        severity = "MEDIUM"
        indicator_tags.append("FailedLogin")
        desc = f"Failed authentication attempt for user '{user_account}' from IP {source_ip}"
        return {
            "timestamp": dt_utc,
            "event_type": event_type,
            "severity": severity,
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "user_account": user_account,
            "description": desc,
            "raw_data": stripped,
            "indicator_tags": ",".join(indicator_tags),
            "auth_outcome": "FAILURE",
        }

    # 2. Accepted authentication
    # e.g.: "Accepted publickey for forensic_user from 192.0.2.15 port 55102 ssh2..."
    accepted_match = re.search(
        r"Accepted (?:publickey|password) for (?:user\s+)?(\w+) from ([\d\.]+) port (\d+)",
        message,
        re.IGNORECASE,
    )
    if accepted_match:
        user_account = accepted_match.group(1)
        source_ip = accepted_match.group(2)
        event_type = "AUTHENTICATION"
        severity = "INFO"
        indicator_tags.append("SuccessfulLogin")
        desc = f"Successful authentication for user '{user_account}' from IP {source_ip}"
        return {
            "timestamp": dt_utc,
            "event_type": event_type,
            "severity": severity,
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "user_account": user_account,
            "description": desc,
            "raw_data": stripped,
            "indicator_tags": ",".join(indicator_tags),
            "auth_outcome": "SUCCESS",
        }

    # 3. Sudo / Privilege Escalation
    # e.g.: "host-sec01 sudo: forensic_user : TTY=pts/0 ; PWD=/home/forensic_user ; USER=root ; COMMAND=/bin/journalctl -u ssh"
    if "sudo" in service.lower() or "sudo" in stripped.lower():
        sudo_match = re.search(r"(\w+)\s*:\s*TTY=.*?USER=(\w+)\s*;\s*COMMAND=(.*)$", message)
        if sudo_match:
            user_account = sudo_match.group(1)
            target_user = sudo_match.group(2)
            command = sudo_match.group(3).strip()
            event_type = "PRIVILEGE_ESCALATION"
            severity = "HIGH" if target_user == "root" else "MEDIUM"
            indicator_tags.extend(["PrivilegeEscalation", "SudoCommand"])
            desc = f"Privilege elevation by user '{user_account}' to '{target_user}': {command}"
            return {
                "timestamp": dt_utc,
                "event_type": event_type,
                "severity": severity,
                "source_ip": source_ip,
                "destination_ip": destination_ip,
                "user_account": user_account,
                "description": desc,
                "raw_data": stripped,
                "indicator_tags": ",".join(indicator_tags),
                "auth_outcome": None,
            }

    # Generic log line fallback
    ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", message)
    if ip_match:
        source_ip = ip_match.group(0)

    return {
        "timestamp": dt_utc,
        "event_type": "LOG_ENTRY",
        "severity": "INFO",
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "user_account": user_account,
        "description": message[:500],
        "raw_data": stripped,
        "indicator_tags": "",
        "auth_outcome": None,
    }


def parse_csv_log_data(content: str) -> List[Dict[str, Any]]:
    """Parse structured CSV security log."""
    reader = csv.DictReader(io.StringIO(content))
    events: List[Dict[str, Any]] = []

    field_map = {
        "timestamp": ["timestamp", "time", "datetime", "date", "event_time"],
        "event_type": ["event_type", "type", "event", "action"],
        "severity": ["severity", "level", "priority"],
        "source_ip": ["source_ip", "src_ip", "src", "client_ip", "ip"],
        "destination_ip": ["destination_ip", "dst_ip", "dst", "server_ip", "target_ip"],
        "user_account": ["user_account", "user", "username", "account"],
        "description": ["description", "message", "details", "desc", "log_message"],
    }

    if not reader.fieldnames:
        return []

    lower_headers = {h.lower().strip(): h for h in reader.fieldnames if h}
    resolved: Dict[str, Optional[str]] = {}

    for target_key, candidate_names in field_map.items():
        found = None
        for candidate in candidate_names:
            if candidate in lower_headers:
                found = lower_headers[candidate]
                break
        resolved[target_key] = found

    for row in reader:
        desc_val = row.get(resolved["description"], "") if resolved["description"] else ""
        type_val = row.get(resolved["event_type"], "SECURITY_EVENT") if resolved["event_type"] else "SECURITY_EVENT"
        time_raw = row.get(resolved["timestamp"], "") if resolved["timestamp"] else ""

        if not desc_val and not type_val:
            continue

        timestamp_utc = parse_timestamp_utc(time_raw) if time_raw else datetime.now(timezone.utc)
        sev_val = row.get(resolved["severity"], "INFO").upper() if resolved["severity"] else "INFO"
        if sev_val not in ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            sev_val = "INFO"

        src_ip = row.get(resolved["source_ip"], None) if resolved["source_ip"] else None
        dst_ip = row.get(resolved["destination_ip"], None) if resolved["destination_ip"] else None
        user = row.get(resolved["user_account"], None) if resolved["user_account"] else None

        outcome = None
        type_upper = type_val.upper()
        if "AUTHENTICATION" in type_upper or "LOGIN" in type_upper or "AUTH" in type_upper:
            type_val = "AUTHENTICATION"
            if "FAIL" in desc_val.upper() or sev_val in ["MEDIUM", "HIGH", "CRITICAL"]:
                outcome = "FAILURE"
            else:
                outcome = "SUCCESS"

        raw_line = ",".join([f"{k}={v}" for k, v in row.items() if v])

        events.append({
            "timestamp": timestamp_utc,
            "event_type": type_val,
            "severity": sev_val,
            "source_ip": src_ip if src_ip else None,
            "destination_ip": dst_ip if dst_ip else None,
            "user_account": user if user else None,
            "description": desc_val or f"Event {type_val}",
            "raw_data": raw_line,
            "indicator_tags": "",
            "auth_outcome": outcome,
        })

    return events


def analyze_security_events(events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Applies deterministic forensic detection rules to normalized security events.

    Detects:
    1. Repeated failed logins from same source IP or user account (Brute force).
    2. Suspicious login sequences (multiple failures followed by success from same source).
    3. Elevated privilege transitions.
    """
    sorted_events = sorted(events, key=lambda e: e["timestamp"])
    findings: List[Dict[str, Any]] = []

    failures_by_ip: Dict[str, List[int]] = {}
    failures_by_user: Dict[str, List[int]] = {}

    for idx, ev in enumerate(sorted_events):
        outcome = ev.get("auth_outcome")
        src_ip = ev.get("source_ip")
        user = ev.get("user_account")

        if outcome == "FAILURE":
            if src_ip:
                failures_by_ip.setdefault(src_ip, []).append(idx)
            if user:
                failures_by_user.setdefault(user, []).append(idx)

    # 1. Rule: Brute Force Threshold (>= 3 failed logins from same IP)
    for ip, indices in failures_by_ip.items():
        if len(indices) >= 3:
            first_time = sorted_events[indices[0]]["timestamp"]
            last_time = sorted_events[indices[-1]]["timestamp"]
            finding = {
                "rule": "BRUTE_FORCE_IP_THRESHOLD",
                "severity": "HIGH",
                "source_ip": ip,
                "failure_count": len(indices),
                "first_seen_utc": first_time.isoformat(),
                "last_seen_utc": last_time.isoformat(),
                "description": f"Repeated authentication failures ({len(indices)} attempts) detected originating from source IP {ip}.",
                "indicator_tags": "T1110,BruteForce,CredentialAccess",
            }
            findings.append(finding)

            for idx in indices:
                tags = sorted_events[idx]["indicator_tags"]
                new_tags = list(filter(None, tags.split(","))) + ["T1110", "BruteForce"]
                sorted_events[idx]["indicator_tags"] = ",".join(sorted(set(new_tags)))
                if sorted_events[idx]["severity"] in ["INFO", "LOW", "MEDIUM"]:
                    sorted_events[idx]["severity"] = "HIGH"

    # 2. Rule: Repeated Failed Logins on Single Account (>= 3 failed attempts)
    for user, indices in failures_by_user.items():
        if len(indices) >= 3:
            finding = {
                "rule": "ACCOUNT_TARGETING_THRESHOLD",
                "severity": "HIGH",
                "user_account": user,
                "failure_count": len(indices),
                "description": f"Targeted authentication attacks detected against user account '{user}' ({len(indices)} failed attempts).",
                "indicator_tags": "T1110.001,PasswordGuessing",
            }
            findings.append(finding)

    # 3. Rule: Suspicious Sequence (Brute Force Followed by Success)
    for idx, ev in enumerate(sorted_events):
        if ev.get("auth_outcome") == "SUCCESS":
            src_ip = ev.get("source_ip")
            if src_ip and src_ip in failures_by_ip:
                prior_failures = [f_idx for f_idx in failures_by_ip[src_ip] if f_idx < idx]
                if len(prior_failures) >= 2:
                    ev["severity"] = "CRITICAL"
                    tags = ev["indicator_tags"]
                    new_tags = list(filter(None, tags.split(","))) + ["T1110", "AccountCompromise", "SuspiciousSequence"]
                    ev["indicator_tags"] = ",".join(sorted(set(new_tags)))
                    ev["description"] = f"[CRITICAL SEQUENCE] Successful login following {len(prior_failures)} prior failed attempts from {src_ip}"

                    findings.append({
                        "rule": "BRUTE_FORCE_SUCCESS_SEQUENCE",
                        "severity": "CRITICAL",
                        "source_ip": src_ip,
                        "user_account": ev.get("user_account"),
                        "timestamp_utc": ev["timestamp"].isoformat(),
                        "prior_failed_count": len(prior_failures),
                        "description": f"High-confidence breach indicator: Successful authentication achieved by user '{ev.get('user_account')}' from {src_ip} immediately following {len(prior_failures)} failed attempts.",
                        "indicator_tags": "T1110,AccountCompromise,InitialAccess",
                    })

    return sorted_events, findings


def parse_and_analyze_log_stream(content: str, filename: str = "") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Auto-detect format (CSV vs Syslog/Auth.log), parse lines, and execute detection rules."""
    stripped = content.strip()
    if not stripped:
        return [], []

    first_line = stripped.splitlines()[0].strip()
    is_csv = ("," in first_line and not first_line.startswith("#")) or filename.lower().endswith(".csv")

    if is_csv:
        raw_events = parse_csv_log_data(content)
    else:
        raw_events = []
        for line in stripped.splitlines():
            parsed = parse_auth_syslog_line(line)
            if parsed:
                raw_events.append(parsed)

    if not raw_events:
        return [], []

    return analyze_security_events(raw_events)
