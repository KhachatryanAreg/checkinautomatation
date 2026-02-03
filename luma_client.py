"""
Luma API client for fetching attendee information by ticket/guest key.
Uses the Get Guest by Key endpoint: GET .../get-guest?id={pk_value}
Authentication: Authorization: Bearer <api_key>
"""

import requests
from typing import Any


# Luma API response may use different field names; we normalize to name + company.
def _normalize_guest(data: dict) -> tuple[str, str]:
    """Extract display name and company from Luma guest object. Returns (name, company)."""
    name = ""
    if isinstance(data.get("name"), str):
        name = data["name"].strip()
    if not name and (data.get("first_name") or data.get("last_name")):
        first = (data.get("first_name") or "").strip()
        last = (data.get("last_name") or "").strip()
        name = f"{first} {last}".strip()
    if not name:
        name = data.get("email") or "—"
    company = (data.get("company") or data.get("organization") or data.get("org") or "").strip() or "—"
    return name, company


def fetch_guest_by_ticket_id(
    ticket_id: str,
    base_url: str,
    api_key: str,
    event_id: str | None = None,
) -> tuple[bool, str, str, str | None]:
    """
    Call Luma API get-guest for the given ticket/guest key.
    ticket_id: the pk value from the QR (e.g. g-abc123 or ticket key from CSV).
    base_url: e.g. https://public-api.luma.com/v1/event (no trailing slash).
    api_key: Luma API key from Calendar → Settings → Developer.
    event_id: optional; some API versions may require it.

    Returns:
        (success, attendee_name, attendee_company, error_message).
        On success: error_message is None. On failure: name/company may be empty, error_message set.
    """
    url = f"{base_url.rstrip('/')}/get-guest"
    params: dict[str, str] = {"id": ticket_id.strip()}
    if event_id:
        params["event_id"] = event_id
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
    except requests.RequestException as e:
        return False, "", "", str(e)
    if r.status_code != 200:
        try:
            body = r.json()
            msg = body.get("message") or body.get("error") or r.text
        except Exception:
            msg = r.text or f"HTTP {r.status_code}"
        return False, "", "", msg
    try:
        data = r.json()
    except Exception as e:
        return False, "", "", f"Invalid JSON: {e}"
    # Consider valid if we got a 200 and something that looks like a guest (e.g. has name or email).
    name, company = _normalize_guest(data)
    if not name and not data.get("email"):
        return False, name or "—", company, "Guest data missing or invalid"
    return True, name, company, None


def check_in_guest(
    ticket_id: str,
    base_url: str,
    api_key: str,
    event_id: str | None = None,
) -> str | None:
    """
    Check in the guest in Luma using update-guest-status (POST).
    ticket_id: same pk value used for get-guest (guest key or ticket key).
    Returns None on success, or an error message string on failure.
    """
    url = f"{base_url.rstrip('/')}/update-guest-status"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    body: dict[str, str | bool] = {"id": ticket_id.strip(), "checked_in": True}
    if event_id:
        body["event_id"] = event_id
    try:
        r = requests.post(url, json=body, headers=headers, timeout=15)
    except requests.RequestException as e:
        return str(e)
    if r.status_code not in (200, 201, 204):
        try:
            data = r.json()
            msg = data.get("message") or data.get("error") or r.text
        except Exception:
            msg = r.text or f"HTTP {r.status_code}"
        return msg
    return None
