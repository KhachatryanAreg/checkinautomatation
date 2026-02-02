"""
Check-in audit log: timestamp, Ranger ID, ticket ID, print status.
Writes to a CSV file for easy review and auditing.
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def _ensure_file_header(path: str) -> None:
    """Create log file with header if it does not exist."""
    p = Path(path)
    if p.exists():
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp_utc", "ranger_id", "ticket_id", "print_status", "attendee_name", "attendee_company"])


def log_checkin(
    log_path: str,
    ranger_id: str,
    ticket_id: str,
    print_status: str,
    attendee_name: str = "",
    attendee_company: str = "",
) -> None:
    """
    Append one check-in record to the audit log CSV.
    print_status: e.g. "Success", "Error", "Invalid ticket", "Print failed".
    """
    _ensure_file_header(log_path)
    row = [
        datetime.utcnow().isoformat() + "Z",
        ranger_id,
        ticket_id,
        print_status,
        attendee_name,
        attendee_company,
    ]
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)
