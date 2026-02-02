"""
Simple GUI for the check-in app: last scanned ticket, attendee name/company,
print status, and retry-print button.
Updates are pushed from the processing thread via a callback/queue.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional


class CheckInGUI:
    def __init__(
        self,
        on_retry_print: Optional[Callable[[], None]] = None,
    ):
        self.on_retry_print = on_retry_print
        self._root: Optional[tk.Tk] = None
        self._last_ticket_var: Optional[tk.StringVar] = None
        self._name_var: Optional[tk.StringVar] = None
        self._company_var: Optional[tk.StringVar] = None
        self._status_var: Optional[tk.StringVar] = None
        self._retry_btn: Optional[ttk.Button] = None
        self._last_result: Optional[dict] = None  # For retry: name, company

    def _build(self) -> None:
        root = tk.Tk()
        root.title("Ranger 2 Check-in — TPL 100")
        root.minsize(320, 220)
        self._root = root

        f = ttk.Frame(root, padding=12)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="Last scanned ticket ID:", font=("Segoe UI", 9)).pack(anchor=tk.W)
        self._last_ticket_var = tk.StringVar(value="—")
        ttk.Label(f, textvariable=self._last_ticket_var, font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)

        ttk.Label(f, text="Attendee name:", font=("Segoe UI", 9)).pack(anchor=tk.W)
        self._name_var = tk.StringVar(value="—")
        ttk.Label(f, textvariable=self._name_var, font=("Segoe UI", 10)).pack(anchor=tk.W)

        ttk.Label(f, text="Company:", font=("Segoe UI", 9)).pack(anchor=tk.W)
        self._company_var = tk.StringVar(value="—")
        ttk.Label(f, textvariable=self._company_var, font=("Segoe UI", 10)).pack(anchor=tk.W)

        ttk.Label(f, text="Print status:", font=("Segoe UI", 9)).pack(anchor=tk.W)
        self._status_var = tk.StringVar(value="—")
        ttk.Label(f, textvariable=self._status_var, font=("Segoe UI", 10)).pack(anchor=tk.W)

        btn_f = ttk.Frame(f)
        btn_f.pack(pady=(8, 0))
        self._retry_btn = ttk.Button(btn_f, text="Retry print", command=self._do_retry, state="disabled")
        self._retry_btn.pack(side=tk.LEFT, padx=(0, 8))

    def _do_retry(self) -> None:
        if self.on_retry_print and self._last_result:
            self.on_retry_print()
        elif not self._last_result:
            messagebox.showinfo("Retry", "No previous check-in to retry.")

    def update_result(
        self,
        ticket_id: str,
        attendee_name: str,
        attendee_company: str,
        print_status: str,
        success: bool,
    ) -> None:
        """Call from any thread; schedules GUI update on main thread."""
        self._last_result = {
            "ticket_id": ticket_id,
            "attendee_name": attendee_name,
            "attendee_company": attendee_company,
        }
        if self._root is None:
            return

        def do_update():
            if self._last_ticket_var:
                self._last_ticket_var.set(ticket_id or "—")
            if self._name_var:
                self._name_var.set(attendee_name or "—")
            if self._company_var:
                self._company_var.set(attendee_company or "—")
            if self._status_var:
                self._status_var.set(print_status)
            if self._retry_btn:
                self._retry_btn.config(state="normal")

        self._root.after(0, do_update)

    def get_last_result(self) -> Optional[dict]:
        """Return last result for retry: attendee_name, attendee_company."""
        return self._last_result

    def run(self) -> None:
        self._build()
        if self._root:
            self._root.mainloop()

    def quit(self) -> None:
        if self._root:
            try:
                self._root.quit()
            except Exception:
                pass
