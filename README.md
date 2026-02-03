# Ranger 2 + TPL 100 Check-in App

Application that checks in guests via the **Luma API** and prints check-in stickers on a **Terra Nova TPL 100** (or default Windows printer). The main interface is the **web page**: open it in a browser or webview, focus the text field, and scan Luma QR codes (or type ticket IDs). Each scan checks in the guest in Luma and prints their sticker.

## Requirements

- Windows notebook (for printing; HTTP server runs on any OS)
- Python 3.8+
- Terra Nova TPL 100 printer (Windows driver installed), or default printer
- Luma Plus subscription and API key (Calendar → Settings → Developer)
- A barcode/QR scanner that acts as a keyboard (types into the focused field and sends Enter), or type ticket IDs manually

## Credentials and what to change

All of this is in **`config.yaml`** (copy from `config.example.yaml`). Do **not** put real secrets in the example file or in code.

| What to change | Where | What to set |
|----------------|-------|-------------|
| **Luma API key** | `config.yaml` → `luma.api_key` | Your Luma API key from **Calendar → Settings → Developer**. Replace `"your-luma-api-key"`. |
| **Printer name** | `config.yaml` → `printer.name` | Windows printer name (e.g. `"Terra Nova TPL 100"`). Leave `""` for default printer. |
| **Listen port** | `config.yaml` → `listen_port` | Port for the app (e.g. `8765`). Change only if this port is in use. |
| **Event ID** (optional) | `config.yaml` → `luma.event_id` | Uncomment and set `"evt-xxx"` if your Luma API requires it. |
| **Luma API base URL** (optional) | `config.yaml` → `luma.base_url` | Only change if Luma changes their API (default is correct). |
| **Check-in log file** | `config.yaml` → `logging.checkin_log_path` | Path for the CSV log (default: `"checkins.csv"`). |

**Optional custom text (in code):**

| What | File | What to edit |
|------|------|--------------|
| Receipt text (title, "Name:", "Company:") | `printer_service.py` | `RECEIPT_TEMPLATE` |
| Web page title, heading, button label | `scan_server.py` | `_PAGE_HTML` (e.g. `<title>`, `<h1>`, button text) |
| Desktop window title | `gui.py` | `root.title("Ranger 2 Check-in — TPL 100")` |

No other credentials or custom names are required in the code; everything else is driven by `config.yaml`.

## Quick Start

1. **Clone/copy** this folder to the notebook.

2. **Create config**  
   Copy `config.example.yaml` to `config.yaml` and set at least:
   - `luma.api_key`: your Luma API key
   - `printer.name`: Windows printer name (e.g. `Terra Nova TPL 100`) or leave empty for default

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
   On Windows, `pywin32` is required for printing.

4. **Run the app**  
   ```bash
   python main.py
   ```

5. **Use the web page (main workflow)**  
   Open the notebook’s **IP** in a browser or on the Ranger:
   - **IP:** `http://<notebook-ip>:<port>` (e.g. `http://192.168.55.82:8765`)
   - Focus the **"Scan QR code or enter ticket ID"** field.
   - Scan a Luma guest/ticket QR code with your barcode scanner (it types the ticket ID and sends Enter), or type the ticket ID and press Enter or click **Check in & print sticker**.
   - The app looks up the guest in Luma, checks them in, and prints their sticker. The page is ready for the next scan.

   The desktop window shows last scan, attendee name/company, and print status; you can use it for retry or monitoring, but the primary interface is the web page.

   **(Optional) Ranger 2 HTTP POST:** If you use a Ranger 2 scanner that sends HTTP POST instead of the web field, set URL to `http://<notebook-ip>:8765/scan`, method POST, and form field `ticket_id` with the scanned barcode.

### "The URL cannot be shown" when opening the page on the Ranger

Many handheld scanners (including Ranger 2) have a built-in browser that **cannot open HTTP or local IP addresses** (e.g. `http://192.168.55.82:8765`), so you get "the url cannot be shown".

**Workaround — use the Ranger as a keyboard scanner:**

1. **Open the check-in page on the notebook** (or on a phone/tablet on the same Wi‑Fi): in a browser go to `http://192.168.55.82:8765`.
2. **Click in the "Scan QR code or enter ticket ID"** field so it’s focused.
3. **Set the Ranger to keyboard/HID mode** (it acts as a keyboard: it types the barcode and sends Enter). Check the Ranger manual for "keyboard wedge" or "HID" mode.
4. **Scan the guest’s QR code** with the Ranger. It will type the ticket ID into the field and send Enter; the form submits, the guest is checked in and the sticker prints.

You never open the URL on the Ranger — you open it on the notebook (or phone) and only use the Ranger to scan into that page. If the Ranger has no keyboard mode, use the optional **Ranger 2 HTTP POST** setup above so the Ranger sends scans to `/scan` instead of loading a page.

**Also check:** Ranger and notebook on the same Wi‑Fi; Windows firewall allows incoming connections on port 8765.

## Features

- **Configurable port** for incoming scans (Ranger 2 → notebook).
- **Luma API**: fetches attendee name and company by ticket/guest key (`get-guest?id=...`).
- **Check-in**: when a valid ticket is scanned, the guest is checked in with Luma (`POST update-guest-status`). Disable with `luma.check_in_on_scan: false` in config.
- **Validation**: invalid ticket → error on screen, no print.
- **Receipt template** (plain text):
  ```
  ---
  Check-in Receipt
  Name: [attendee_name]
  Company: [attendee_company]
  ---
  ```
- **Printing**: Windows raw text to TPL 100 (or default printer); immediate print via `win32print`.
- **Real-time handling**: one scan at a time, no merging of data from different Rangers.
- **Audit log**: CSV with timestamp, Ranger ID, ticket ID, print status (see `config.logging.checkin_log_path`).
- **GUI**: last ticket ID, attendee name/company, print status (Success/Error), **Retry print** for last check-in.

## Project layout (modular)

| File | Purpose |
|------|--------|
| `config.py` | Loads `config.yaml`; change port, Luma URL/key, printer, log path here. |
| `luma_client.py` | Luma API client (get-guest, update-guest-status for check-in). Swap or extend for different Luma endpoints. |
| `printer_service.py` | Format receipt and send to Windows printer. Change template or add ESC/POS here. |
| `checkin_logger.py` | Append check-ins to CSV for auditing. |
| `scan_server.py` | Flask HTTP server for Ranger 2 POST; enqueues scans. |
| `gui.py` | Tkinter UI: last scan, name, company, status, retry. |
| `main.py` | Ties config, server, queue, worker, and GUI together. |

To support another printer model or API: adjust `printer_service.py` (e.g. different driver or ESC/POS commands) or `luma_client.py` (e.g. different base URL or auth).

## Log file

Check-ins are appended to the file set in `config.logging.checkin_log_path` (default: `checkins.csv`) with columns:

- `timestamp_utc`
- `ranger_id`
- `ticket_id`
- `print_status`
- `attendee_name`
- `attendee_company`

## Luma API

- **Get guest**: `GET https://public-api.luma.com/v1/event/get-guest?id={pk_value}`
- **Check-in**: `POST https://public-api.luma.com/v1/event/update-guest-status` with JSON `{"id": "<pk_value>", "checked_in": true}`
- Auth: `Authorization: Bearer <your-api-key>`
- `pk_value`: guest key (e.g. `g-abc123`) or ticket key from CSV export.

## License

Use and modify as needed for your environment.
