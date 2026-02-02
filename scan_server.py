"""
HTTP server that receives scan events from Moveast Ranger 2 barcode scanners.
Ranger 2 can be configured to send HTTP POST with the scanned barcode (ticket ID).
This server listens on a configurable port and enqueues each scan for processing
so that multiple scans are handled in real-time without merging data from different Rangers.
"""

import threading
from typing import Callable

from flask import Flask, request, jsonify

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

    @app.route("/scan", methods=["POST"])
    def scan():
        # Accept JSON: { "ticket_id": "...", "ranger_id": "..." }
        # or form: ticket_id=...&ranger_id=...
        ticket_id = ""
        ranger_id = ""
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
            return jsonify({"ok": False, "error": "Missing ticket_id"}), 400
        if not ranger_id:
            ranger_id = "default"
        try:
            on_scan(ranger_id, ticket_id)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500
        return jsonify({"ok": True, "ticket_id": ticket_id, "ranger_id": ranger_id}), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    def run_server():
        app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)

    thread = threading.Thread(target=run_server, daemon=True)
    return app, thread
