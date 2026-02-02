# Ranger 2 + TPL 100 Check-in App

Cross-platform (Windows-focused) application that connects **Moveast Ranger 2** barcode scanners to **Terra Nova TPL 100** printers using the **Luma API**. Each Ranger 2 is paired with one notebook; the app receives scanned ticket IDs via HTTP POST, fetches attendee data from Luma, validates the ticket, and prints a check-in receipt.

## Requirements

- Windows notebook (for printing; HTTP server runs on any OS)
- Python 3.8+
- Moveast Ranger 2 scanner(s) configured to POST to this app
- Terra Nova TPL 100 printer (Windows driver installed)
- Luma Plus subscription and API key (Calendar → Settings → Developer)

## Quick Start

1. **Clone/copy** this folder to the notebook.

2. **Create config**  
   Copy `config.example.yaml` to `config.yaml` and set:
   - `listen_port`: local port for receiving scans (e.g. `8765`)
   - `luma.api_key`: your Luma API key
   - `printer.name`: Windows printer name (e.g. `Terra Nova TPL 100`) or leave empty for default printer

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
   On Windows, `pywin32` is required for printing.

4. **Run the app**  
   ```bash
   python main.py
   ```
   - Scan server: `http://<notebook-ip>:<listen_port>/scan`
   - GUI shows last scan, attendee name/company, print status, and **Retry print**.

5. **Configure Ranger 2**  
   Set the scanner to send HTTP POST to:
   - URL: `http://<notebook-ip>:<port>/scan`
   - Body: JSON `{"ticket_id": "<scanned_barcode>", "ranger_id": "<optional_scanner_id>"}`  
   Or form: `ticket_id=<barcode>&ranger_id=<id>`  
   (Exact fields depend on Ranger 2 firmware; the app accepts `ticket_id` / `ticket` / `barcode` and `ranger_id` / `scanner_id`.)

## Features

- **Configurable port** for incoming scans (Ranger 2 → notebook).
- **Luma API**: fetches attendee name and company by ticket/guest key (`get-guest?id=...`).
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
| `luma_client.py` | Luma API client (get-guest). Swap or extend for different Luma endpoints. |
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

- Endpoint: `GET https://public-api.luma.com/v1/event/get-guest?id={pk_value}`
- Auth: `Authorization: luma-api-key=<your-api-key>`
- `pk_value`: guest key (e.g. `g-abc123`) or ticket key from CSV export.

## License

Use and modify as needed for your environment.
