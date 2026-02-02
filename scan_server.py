"""
HTTP server that receives scan events from Moveast Ranger 2 barcode scanners.
Ranger 2 can be configured to send HTTP POST with the scanned barcode (ticket ID).
This server listens on a configurable port and enqueues each scan for processing
so that multiple scans are handled in real-time without merging data from different Rangers.
"""

import threading
from typing import Callable

from html import escape as _h
from urllib.parse import quote

from flask import Flask, request, jsonify, redirect

_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Check-in — Scan QR · Print sticker</title>
  <style>
    body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 420px; margin: 2rem auto; padding: 0 1rem; background: #F0F4FF; color: #1E293B; }}
    h1 {{ font-size: 1.35rem; color: #2563EB; margin-bottom: 0.5rem; }}
    p {{ color: #334155; font-size: 0.95rem; line-height: 1.5; }}
    .msg {{ padding: 0.6rem; border-radius: 8px; margin-bottom: 1rem; font-size: 0.9rem; }}
    .msg.ok {{ background: #D1FAE5; color: #047857; border: 1px solid #059669; }}
    .msg.err {{ background: #FEE2E2; color: #B91C1C; border: 1px solid #DC2626; }}
    label {{ display: block; color: #7C3AED; font-weight: 600; font-size: 0.9rem; margin-bottom: 0.35rem; }}
    input[type="text"] {{ width: 100%; padding: 0.6rem; font-size: 1rem; box-sizing: border-box; border: 2px solid #2563EB; border-radius: 6px; background: #FFFFFF; }}
    input:focus {{ outline: none; border-color: #7C3AED; }}
    button {{ margin-top: 0.5rem; padding: 0.6rem 1.2rem; font-size: 1rem; cursor: pointer; background: #2563EB; color: #FFFFFF; border: none; border-radius: 6px; font-weight: 600; }}
    button:hover {{ background: #1D4ED8; }}
    .hint {{ color: #059669; font-size: 0.85rem; margin-top: 0.25rem; }}
  </style>
</head>
<body>
  <h1>Check in guest · Print sticker</h1>
  <p>Use the text field below. Scan a Luma QR code with your barcode scanner (it types the ticket ID and sends Enter), or type the ticket ID and press Enter. The guest is checked in and their sticker is printed.</p>
  {message}
  <form method="post" action="/scan" id="scanForm">
    <label for="ticket_id">Scan QR code or enter ticket ID</label>
    <input type="text" id="ticket_id" name="ticket_id" placeholder="Focus here, then scan QR…" autofocus autocomplete="off">
    <p class="hint">Keep this page open; after each scan the field is ready for the next guest.</p>
    <br>
    <button type="submit">Check in &amp; print sticker</button>
  </form>
</body>
</html>
"""


def create_scan_server(
    port: int,
    on_scan: Callable[[str, str], None],
) -> tuple[Flask, threading.Thread]:
    """
    Create a Flask app that accepts POST with ticket_id (and optional ranger_id),
    and a background thread running the server.
    on_scan(ranger_id, ticket_id) is called for each scan; implement thread-safe handling inside.
    """
    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def root():
        submitted = request.args.get("submitted")
        ticket_id = request.args.get("ticket_id", "")
        err = request.args.get("error", "")
        msg = ""
        if submitted and ticket_id:
            msg = f'<p class="msg ok">Check-in submitted for <strong>{_h(ticket_id)}</strong>. The app will process it.</p>'
        elif err:
            msg = f'<p class="msg err">Error: {_h(err)}</p>'
        html = _PAGE_HTML.format(message=msg)
        return html, 200, {"Content-Type": "text/html; charset=utf-8"}

    @app.route("/favicon.ico", methods=["GET"])
    def favicon():
        return "", 204

    @app.route("/scan", methods=["POST"])
    def scan():
        # Accept JSON: { "ticket_id": "...", "ranger_id": "..." }
        # or form: ticket_id=...&ranger_id=... (e.g. from the web page text field)
        ticket_id = ""
        ranger_id = ""
        is_form = not request.is_json and request.content_type and "application/x-www-form-urlencoded" in (request.content_type or "")
        if request.is_json:
            data = request.get_json(silent=True) or {}
            ticket_id = (data.get("ticket_id") or data.get("ticket") or data.get("barcode") or "").strip()
            ranger_id = (data.get("ranger_id") or data.get("scanner_id") or data.get("ranger") or "").strip()
        else:
            ticket_id = (request.form.get("ticket_id") or request.form.get("ticket") or request.form.get("barcode") or "").strip()
            ranger_id = (request.form.get("ranger_id") or request.form.get("scanner_id") or request.form.get("ranger") or "").strip()
        # Some scanners send raw body as the barcode
        if not ticket_id and request.get_data(as_text=True):
            ticket_id = request.get_data(as_text=True).strip()
        if not ticket_id:
            if is_form:
                return redirect("/?error=" + quote("Missing ticket ID"))
            return jsonify({"ok": False, "error": "Missing ticket_id"}), 400
        if not ranger_id:
            ranger_id = "web"
        try:
            on_scan(ranger_id, ticket_id)
        except Exception as e:
            if is_form:
                return redirect("/?error=" + quote(str(e)))
            return jsonify({"ok": False, "error": str(e)}), 500
        if is_form:
            return redirect("/?submitted=1&ticket_id=" + quote(ticket_id))
        return jsonify({"ok": True, "ticket_id": ticket_id, "ranger_id": ranger_id}), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    def run_server():
        app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)

    thread = threading.Thread(target=run_server, daemon=True)
    return app, thread
