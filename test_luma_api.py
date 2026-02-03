"""
Test if the Luma API key in config.yaml works.
Calls the get-guest endpoint; response indicates whether the key is valid.
Run: python test_luma_api.py
"""

import sys
from config import load_config, get_luma_settings
import requests


def test_luma_api_key() -> None:
    config = load_config()
    luma = get_luma_settings(config)
    base_url = (luma.get("base_url") or "").strip()
    api_key = (luma.get("api_key") or "").strip()
    event_id = (luma.get("event_id") or "").strip() or None

    if not api_key or api_key == "your-luma-api-key":
        print("Error: No API key set. Edit config.yaml and set luma.api_key to your Luma API key.")
        sys.exit(1)

    url = f"{base_url.rstrip('/')}/get-guest"
    params = {"id": "test-key-validation"}
    if event_id:
        params["event_id"] = event_id
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    print("Testing Luma API key...")
    print(f"  URL: {url}")
    print(f"  (using a test id to check auth only)")
    print()

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
    except requests.RequestException as e:
        print(f"Connection error: {e}")
        sys.exit(1)

    if r.status_code == 200:
        print("OK: API key is valid. Request succeeded (get-guest returned 200).")
        try:
            data = r.json()
            if data and (data.get("name") or data.get("email") or data.get("id")):
                print("     (A guest record was returned; you can use this key for check-in.)")
            else:
                print("     (Empty or test response; key is still valid.)")
        except Exception:
            print("     (Response is valid.)")
        return

    if r.status_code == 401:
        print("FAIL: API key is invalid or not accepted (401 Unauthorized).")
        print("      Check that luma.api_key in config.yaml matches your key from")
        print("      Luma Calendar → Settings → Developer.")
        sys.exit(1)

    if r.status_code == 403:
        print("FAIL: API key was rejected (403 Forbidden).")
        print("      Your key may not have permission for this endpoint or event.")
        sys.exit(1)

    if r.status_code in (404, 400):
        print("OK: API key appears valid. The server accepted the request and responded")
        print("    with 'not found' or 'bad request' for the test id (expected).")
        try:
            body = r.json()
            msg = body.get("message") or body.get("error") or r.text[:200]
            if msg:
                print(f"    Response: {msg}")
        except Exception:
            pass
        return

    print(f"Unexpected response: HTTP {r.status_code}")
    try:
        print(r.json())
    except Exception:
        print(r.text[:500])
    sys.exit(1)


if __name__ == "__main__":
    test_luma_api_key()
