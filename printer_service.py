"""
Printing service for Terra Nova TPL 100 (or any Windows printer).
Supports:
  - Windows: raw text/ESC-POS via win32print (immediate raw data).
  - Windows: by printer name or default printer.
To support other printer models, add a new backend here or swap printer name in config.
"""

import sys
from typing import Optional

# Receipt template as specified (plain text).
RECEIPT_TEMPLATE = """---
Check-in Receipt
Name: {attendee_name}
Company: {attendee_company}
---
"""


def format_receipt(attendee_name: str, attendee_company: str) -> str:
    """Format the check-in receipt text. Override or change template here for different layouts."""
    return RECEIPT_TEMPLATE.format(
        attendee_name=attendee_name,
        attendee_company=attendee_company,
    )


def _print_windows_raw(printer_name: Optional[str], text: str) -> Optional[str]:
    """
    Send raw text to a Windows printer. Uses default printer if printer_name is empty.
    Returns None on success, or an error message string.
    """
    if sys.platform != "win32":
        return "Windows-only: install and run on Windows for printing."
    try:
        import win32print
    except ImportError:
        return "pywin32 not installed. Run: pip install pywin32"
    name = (printer_name or "").strip()
    if not name:
        try:
            name = win32print.GetDefaultPrinter()
        except Exception as e:
            return f"No default printer: {e}"
    try:
        h = win32print.OpenPrinter(name)
    except Exception as e:
        return f"OpenPrinter failed: {e}"
    try:
        win32print.StartDocPrinter(h, 1, ("Check-in Receipt", None, "RAW"))
        try:
            win32print.StartPagePrinter(h)
            # Send as bytes; printer often expects UTF-8 or CP437 for receipt.
            raw = text.encode("utf-8", errors="replace")
            win32print.WritePrinter(h, raw)
            win32print.EndPagePrinter(h)
        finally:
            win32print.EndDocPrinter(h)
    except Exception as e:
        return str(e)
    finally:
        win32print.ClosePrinter(h)
    return None


def print_receipt(
    attendee_name: str,
    attendee_company: str,
    printer_name: Optional[str] = None,
    use_raw: bool = True,
) -> Optional[str]:
    """
    Print the check-in receipt to the configured printer.
    printer_name: Windows printer name; empty = default printer.
    use_raw: True = send raw text (recommended for thermal receipt); False = same path, still raw (driver-dependent).
    Returns None on success, or an error message string.
    """
    text = format_receipt(attendee_name, attendee_company)
    return _print_windows_raw(printer_name, text)
