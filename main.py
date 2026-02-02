"""
Main entry point: starts HTTP server for Ranger 2 scans, processes each scan
(Luma API -> validate -> print -> log), and runs the GUI.
Each scan is processed one at a time so data from different Rangers is never merged.
"""

import queue
import threading
from typing import Optional

from config import load_config, get_listen_port, get_luma_settings, get_printer_settings, get_log_settings
from luma_client import fetch_guest_by_ticket_id
from printer_service import print_receipt
from checkin_logger import log_checkin
from scan_server import create_scan_server
from gui import CheckInGUI


def process_one_scan(
    ranger_id: str,
    ticket_id: str,
    config: dict,
    gui: Optional[CheckInGUI],
) -> None:
    """
    For a single scan: fetch guest from Luma, validate, print receipt, log.
    Updates GUI with result. No data from other scans is used.
    """
    luma = get_luma_settings(config)
    printer = get_printer_settings(config)
    log_cfg = get_log_settings(config)
    base_url = (luma.get("base_url") or "").strip()
    api_key = (luma.get("api_key") or "").strip()
    event_id = (luma.get("event_id") or "").strip() or None
    printer_name = (printer.get("name") or "").strip() or None
    use_raw = bool(printer.get("use_raw", True))
    log_path = (log_cfg.get("checkin_log_path") or "checkins.csv").strip()

    # 1) Fetch attendee from Luma
    ok, attendee_name, attendee_company, error_msg = fetch_guest_by_ticket_id(
        ticket_id, base_url, api_key, event_id
    )

    if not ok:
        print_status = f"Error: {error_msg or 'Invalid ticket'}"
        log_checkin(log_path, ranger_id, ticket_id, print_status, attendee_name, attendee_company)
        if gui:
            gui.update_result(ticket_id, attendee_name or "—", attendee_company or "—", print_status, False)
        return

    # 2) Validate: we consider valid if Luma returned 200 and we got a name (or email)
    # Already ensured in fetch_guest_by_ticket_id.

    # 3) Print receipt
    err = print_receipt(attendee_name, attendee_company, printer_name=printer_name, use_raw=use_raw)
    if err:
        print_status = f"Error: {err}"
    else:
        print_status = "Success"

    # 4) Log
    log_checkin(log_path, ranger_id, ticket_id, print_status, attendee_name, attendee_company)

    # 5) Update GUI
    if gui:
        gui.update_result(ticket_id, attendee_name, attendee_company, print_status, err is None)


def worker_loop(
    scan_queue: queue.Queue,
    config: dict,
    gui: Optional[CheckInGUI],
) -> None:
    """Process scans from the queue one at a time (no merging)."""
    while True:
        try:
            item = scan_queue.get()
            if item is None:
                break
            ranger_id, ticket_id = item
            process_one_scan(ranger_id, ticket_id, config, gui)
        except Exception:
            pass
        finally:
            try:
                scan_queue.task_done()
            except Exception:
                pass


def main() -> None:
    config = load_config()
    port = get_listen_port(config)
    scan_queue: queue.Queue = queue.Queue()

    gui = CheckInGUI()

    def on_scan(ranger_id: str, ticket_id: str) -> None:
        scan_queue.put((ranger_id, ticket_id))

    _, server_thread = create_scan_server(port, on_scan)
    server_thread.start()

    worker = threading.Thread(
        target=worker_loop,
        args=(scan_queue, config, gui),
        daemon=True,
    )
    worker.start()

    def retry_print() -> None:
        last = gui.get_last_result()
        if not last:
            return
        printer = get_printer_settings(config)
        printer_name = (printer.get("name") or "").strip() or None
        use_raw = bool(printer.get("use_raw", True))
        err = print_receipt(
            last["attendee_name"],
            last["attendee_company"],
            printer_name=printer_name,
            use_raw=use_raw,
        )
        if gui:
            gui.update_result(
                last.get("ticket_id", ""),
                last.get("attendee_name", ""),
                last.get("attendee_company", ""),
                "Success" if err is None else f"Error: {err}",
                err is None,
            )

    gui.on_retry_print = retry_print

    print(f"Scan server listening on http://0.0.0.0:{port}/scan")
    print("Configure Ranger 2 to POST ticket_id (and optional ranger_id) to this URL.")
    gui.run()


if __name__ == "__main__":
    main()
