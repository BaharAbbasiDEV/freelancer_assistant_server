"""
Freelancer Assistant MCP Server
--------------------------------
A Model Context Protocol (MCP) server built for freelancers: manage clients
and generate professional, styled HTML invoices through natural language.

This is the most advanced of the three portfolio projects. It combines:
- Local data storage (like project 1: notes-mcp-server)
- Live external data / currency conversion (like project 2: currency-news-server)
- Generated, styled output files (new skill: producing a polished deliverable)

Tools:
1. add_client       -> save a client's info
2. create_invoice   -> generate a styled HTML invoice for a client
3. list_invoices    -> list all invoices created so far
"""

from mcp.server.fastmcp import FastMCP
import json
import os
import urllib.request
from datetime import date

mcp = FastMCP("freelancer-assistant")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENTS_FILE = os.path.join(BASE_DIR, "clients.json")
INVOICES_FILE = os.path.join(BASE_DIR, "invoices.json")
INVOICES_DIR = os.path.join(BASE_DIR, "invoices")

os.makedirs(INVOICES_DIR, exist_ok=True)


# ---------- storage helpers ----------

def _load(path: str) -> list:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save(path: str, data: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_exchange_rate(base: str, target: str):
    """Best-effort live rate lookup. Returns None on any failure."""
    try:
        url = f"https://open.er-api.com/v6/latest/{base.upper()}"
        with urllib.request.urlopen(url, timeout=8) as response:
            data = json.loads(response.read().decode())
        if data.get("result") == "success":
            return data.get("rates", {}).get(target.upper())
    except Exception:
        return None
    return None


# ---------- tools ----------

@mcp.tool()
def add_client(name: str, email: str = "", notes: str = "") -> str:
    """Add a new client to your client list.

    Args:
        name: The client's full name or company name.
        email: Optional contact email.
        notes: Optional notes (e.g. how you met, project type).
    """
    clients = _load(CLIENTS_FILE)
    clients.append({"name": name, "email": email, "notes": notes})
    _save(CLIENTS_FILE, clients)
    return f"Client '{name}' added. You now have {len(clients)} client(s)."


@mcp.tool()
def create_invoice(
    client_name: str,
    items: str,
    currency: str = "USD",
    secondary_currency: str = "",
) -> str:
    """Create a professional, styled HTML invoice for a client and save it as a file.

    Args:
        client_name: The name of the client being billed.
        items: A comma-separated list of "description:amount" pairs,
               e.g. "Logo design:150, Homepage build:400".
        currency: 3-letter currency code for the invoice (default "USD").
        secondary_currency: Optional 3-letter code to also show the total
                             converted into (e.g. "IRR"). Leave empty to skip.
    """
    # Parse items
    line_items = []
    for chunk in items.split(","):
        if ":" not in chunk:
            continue
        desc, amount_str = chunk.rsplit(":", 1)
        try:
            amount = float(amount_str.strip())
        except ValueError:
            continue
        line_items.append((desc.strip(), amount))

    if not line_items:
        return (
            'No valid items found. Use the format: '
            '"Description:amount, Description:amount" e.g. "Logo design:150, Homepage:400"'
        )

    total = sum(amount for _, amount in line_items)

    # Optional secondary currency conversion
    secondary_line = ""
    if secondary_currency:
        rate = _get_exchange_rate(currency, secondary_currency)
        if rate:
            converted = total * rate
            secondary_line = f"<p class='secondary'>&asymp; {converted:,.2f} {secondary_currency.upper()}</p>"

    invoices = _load(INVOICES_FILE)
    invoice_number = f"INV-{len(invoices) + 1:04d}"
    today = date.today().isoformat()

    rows_html = "\n".join(
        f"<tr><td>{desc}</td><td class='amount'>{amount:,.2f} {currency.upper()}</td></tr>"
        for desc, amount in line_items
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Invoice {invoice_number}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f5f7; margin: 0; padding: 40px; }}
  .invoice {{ max-width: 700px; margin: 0 auto; background: #ffffff; border-radius: 10px;
              box-shadow: 0 4px 18px rgba(0,0,0,0.08); padding: 40px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start;
             border-bottom: 3px solid #4f46e5; padding-bottom: 20px; margin-bottom: 30px; }}
  .header h1 {{ color: #4f46e5; margin: 0; font-size: 28px; }}
  .header .meta {{ text-align: right; color: #555; font-size: 14px; }}
  .billto {{ margin-bottom: 30px; }}
  .billto span {{ color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .billto p {{ margin: 4px 0 0; font-size: 18px; font-weight: 600; color: #222; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
  th {{ text-align: left; background: #f4f5f7; color: #555; font-size: 13px;
        text-transform: uppercase; padding: 10px 12px; }}
  td {{ padding: 12px; border-bottom: 1px solid #eee; color: #333; }}
  td.amount, th.amount {{ text-align: right; }}
  .total-row {{ display: flex; justify-content: flex-end; margin-top: 10px; }}
  .total-box {{ text-align: right; }}
  .total-box .total {{ font-size: 24px; font-weight: 700; color: #4f46e5; }}
  .secondary {{ color: #888; font-size: 14px; margin: 2px 0 0; }}
  .footer {{ margin-top: 40px; text-align: center; color: #aaa; font-size: 12px; }}
</style>
</head>
<body>
  <div class="invoice">
    <div class="header">
      <h1>INVOICE</h1>
      <div class="meta">
        <div><strong>{invoice_number}</strong></div>
        <div>{today}</div>
      </div>
    </div>
    <div class="billto">
      <span>Billed to</span>
      <p>{client_name}</p>
    </div>
    <table>
      <thead>
        <tr><th>Description</th><th class="amount">Amount</th></tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
    <div class="total-row">
      <div class="total-box">
        <div class="total">{total:,.2f} {currency.upper()}</div>
        {secondary_line}
      </div>
    </div>
    <div class="footer">Generated automatically by Freelancer Assistant (MCP)</div>
  </div>
</body>
</html>
"""

    filename = f"{invoice_number}_{client_name.replace(' ', '_')}.html"
    filepath = os.path.join(INVOICES_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    invoices.append(
        {
            "number": invoice_number,
            "client": client_name,
            "total": total,
            "currency": currency.upper(),
            "date": today,
            "file": filepath,
        }
    )
    _save(INVOICES_FILE, invoices)

    return (
        f"Invoice {invoice_number} created for {client_name}: "
        f"{total:,.2f} {currency.upper()}.\nSaved to: {filepath}"
    )


@mcp.tool()
def list_invoices() -> str:
    """List all invoices created so far, with their number, client, total and date."""
    invoices = _load(INVOICES_FILE)
    if not invoices:
        return "No invoices created yet."
    lines = [
        f"{inv['number']} — {inv['client']} — {inv['total']:,.2f} {inv['currency']} — {inv['date']}"
        for inv in invoices
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
