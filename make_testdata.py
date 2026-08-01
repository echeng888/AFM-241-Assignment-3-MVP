"""
Generates the synthetic test corpus for the AFM 241 MVP.

NOTHING HERE IS REAL CLIENT DATA. Every security, balance, name and transaction
below was invented by us for testing. No Baker Tilly file was seen or used.

Outputs:
  out/statements_FY2025.pdf   12 monthly brokerage statement pages
  out/slips_FY2025.pdf        T5 and T3 slips for the same account/year
  out/ground_truth.csv        the correct answer, for scoring
"""
import csv, os, json
from weasyprint import HTML

OUT = "out"
os.makedirs(OUT, exist_ok=True)

ACCOUNT = "NG-4471902"
CLIENT = "1478223 Ontario Inc."
BROKER = "Northgate Securities Inc."
FY = "2025"

# ---------------------------------------------------------------------------
# The transaction stream. `truth` fields are the ground truth for scoring and
# are NOT printed on the statement.
#   month, date, security, description_as_printed, qty, gross, ccy
#   truth_type, truth_complex (why it must be flagged, "" = routine)
# ---------------------------------------------------------------------------
TXNS = [
    # Jan
    (1, "2025-01-06", "Canadian Utility Trust Units", "PURCHASE - CUT.UN", 400, -9840.00, "CAD", "buy", ""),
    (1, "2025-01-15", "Meridian Bank Common", "DIVIDEND CR", None, 612.50, "CAD", "dividend", ""),
    (1, "2025-01-31", "Cash Balance", "INTEREST PAID ON CREDIT BAL", None, 41.18, "CAD", "interest", ""),
    # Feb
    (2, "2025-02-12", "Canadian Utility Trust Units", "RET OF CAP DIST", None, 288.00, "CAD",
     "return_of_capital", "Return of capital - reduces ACB, does not tie to slip income"),
    (2, "2025-02-20", "Northbridge Energy Corp", "SELL - PARTIAL", -300, 7215.00, "CAD", "sell", ""),
    (2, "2025-02-28", "Cash Balance", "INTEREST PAID ON CREDIT BAL", None, 38.90, "CAD", "interest", ""),
    # Mar
    (3, "2025-03-10", "Meridian Bank Common", "PURCHASE", 150, -8925.00, "CAD", "buy", ""),
    (3, "2025-03-18", "Halcyon Global Income Fund", "DIV REINVEST - 14 SH", 14, 462.00, "CAD",
     "dividend", "Distribution paid in shares - income plus a new parcel with its own cost base at this date"),
    (3, "2025-03-31", "Cash Balance", "INTEREST PAID ON CREDIT BAL", None, 44.02, "CAD", "interest", ""),
    # Apr
    (4, "2025-04-09", "Ridgeline Industrial Inc", "SELL", -200, 5480.00, "CAD", "sell", ""),
    (4, "2025-04-22", "Meridian Bank Common", "DIVIDEND CR", None, 703.75, "CAD", "dividend", ""),
    # May
    (5, "2025-05-14", "Canadian Utility Trust Units", "ROC", None, 288.00, "CAD",
     "return_of_capital", "Return of capital - same treatment, different printed abbreviation"),
    (5, "2025-05-27", "Atlas Materials Ltd", "PURCHASE", 500, -6150.00, "CAD", "buy", ""),
    (5, "2025-05-31", "Cash Balance", "INTEREST PAID ON CREDIT BAL", None, 36.44, "CAD", "interest", ""),
    # Jun
    (6, "2025-06-11", "Northbridge Energy Corp", "PLAN OF ARRANGEMENT - EXCHANGED FOR CASCADE RESOURCES 0.75:1",
     -700, 0.00, "CAD", "transfer",
     "Merger / plan of arrangement - continuity of holding, not a disposal and repurchase"),
    (6, "2025-06-11", "Cascade Resources Ltd", "PLAN OF ARRANGEMENT - RECEIVED", 525, 0.00, "CAD", "transfer",
     "Merger / plan of arrangement - receiving leg; cost base carries over"),
    (6, "2025-06-30", "Cash Balance", "INTEREST PAID ON CREDIT BAL", None, 39.71, "CAD", "interest", ""),
    # Jul
    (7, "2025-07-08", "Fairview Semiconductor Inc (USD)", "SELL - USD ACCT", -120, 9840.00, "USD",
     "sell", "USD-denominated holding acquired 2009 - cost base held in original currency at original date"),
    (7, "2025-07-23", "Meridian Bank Common", "DIVIDEND CR", None, 703.75, "CAD", "dividend", ""),
    # Aug
    (8, "2025-08-15", "Halcyon Global Income Fund", "CASH DIST - SEE T3", None, 1150.00, "CAD",
     "dividend", "Trust distribution - character not determinable from the statement, depends on the T3"),
    (8, "2025-08-29", "Cash Balance", "INTEREST PAID ON CREDIT BAL", None, 42.60, "CAD", "interest", ""),
    # Sep
    (9, "2025-09-12", "Atlas Materials Ltd", "PURCHASE", 250, -3175.00, "CAD", "buy", ""),
    (9, "2025-09-30", "Cash Balance", "INTEREST PAID ON CREDIT BAL", None, 37.85, "CAD", "interest", ""),
    # Oct
    (10, "2025-10-17", "Meridian Bank Common", "DIVIDEND CR", None, 703.75, "CAD", "dividend", ""),
    (10, "2025-10-24", "Ridgeline Industrial Inc", "DELIVERY OUT - IN KIND - 150 SH TO SHAREHOLDER ACCT",
     -150, 0.00, "CAD", "withdrawal",
     "In-kind withdrawal of shares - not a sale; deemed disposition and shareholder benefit questions"),
    # Nov
    (11, "2025-11-07", "Cash Balance", "FUNDS TRANSFER OUT - SHAREHOLDER", None, -25000.00, "CAD",
     "withdrawal", "Shareholder draw - not portfolio activity; affects cost base and shareholder accounts"),
    (11, "2025-11-28", "Canadian Utility Trust Units", "RETURN OF CAPITAL - NON-TAXABLE DIST", None, 288.00, "CAD",
     "return_of_capital", "Return of capital - third printed variant of the same treatment"),
    # Dec
    (12, "2025-12-15", "Meridian Bank Common", "DIVIDEND CR", None, 703.75, "CAD", "dividend", ""),
    (12, "2025-12-31", "Cash Balance", "INTEREST PAID ON CREDIT BAL", None, 40.05, "CAD", "interest", ""),
]

# Opening cost base per security (prior-year closing working paper)
OPENING = [
    ("Meridian Bank Common", 1250, 74375.00, "CAD", ""),
    ("Northbridge Energy Corp", 1000, 21400.00, "CAD", ""),
    ("Ridgeline Industrial Inc", 350, 9012.50, "CAD", ""),
    ("Canadian Utility Trust Units", 1200, 28560.00, "CAD", ""),
    ("Fairview Semiconductor Inc (USD)", 300, 14100.00, "USD", "Acquired 2009-05-18 in USD"),
]

# Slips. The T5 interest is deliberately $6.40 higher than the statements total,
# to test whether the tool surfaces a variance instead of absorbing it.
SLIPS = {
    "T5_dividends_actual": 3427.50,   # ties to the four Meridian dividends
    "T5_interest": 327.15,            # statements total 320.75 -> deliberate variance of 6.40
    "T3_distributions": 1612.00,      # Halcyon 462.00 + 1150.00
}

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]

def money(v, ccy="CAD"):
    if v is None: return ""
    s = f"{abs(v):,.2f}"
    return f"({s})" if v < 0 else s

# --------------------------- statement PDF ---------------------------------
CSS = """
@page { size: Letter; margin: 16mm 15mm; }
body { font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 8pt; color:#111; }
.hdr { border-bottom: 2px solid #1b3a5c; padding-bottom:4mm; margin-bottom:5mm; }
.broker { font-size: 15pt; font-weight:bold; color:#1b3a5c; letter-spacing:.5px; }
.sub { font-size:7.5pt; color:#555; }
.meta { width:100%; margin:4mm 0 5mm 0; font-size:8pt; }
.meta td { padding:1mm 0; }
.meta .lbl { color:#555; width:32mm; }
h2 { font-size:9pt; color:#1b3a5c; margin:5mm 0 2mm 0; border-bottom:1px solid #1b3a5c; padding-bottom:1mm;}
table.txn { width:100%; border-collapse:collapse; font-size:7.6pt; }
table.txn th { background:#eef2f6; text-align:left; padding:1.6mm 1.5mm; border-bottom:1px solid #b8c4d0; font-size:7pt; text-transform:uppercase; letter-spacing:.4px;}
table.txn td { padding:1.5mm 1.5mm; border-bottom:1px solid #e3e8ee; vertical-align:top; }
td.r { text-align:right; font-variant-numeric: tabular-nums; }
.foot { margin-top:6mm; font-size:6.6pt; color:#777; border-top:1px solid #ccc; padding-top:2mm; }
.pg { page-break-after: always; }
.pg:last-child { page-break-after: auto; }
.none { color:#777; font-style:italic; padding:3mm 0; }
"""

pages = []
for m in range(1, 13):
    rows = [t for t in TXNS if t[0] == m]
    body = ""
    if rows:
        body = "<table class='txn'><thead><tr><th style='width:20mm'>Date</th><th style='width:52mm'>Security</th><th>Description</th><th style='width:18mm' class='r'>Quantity</th><th style='width:24mm' class='r'>Amount</th><th style='width:12mm'>Curr</th></tr></thead><tbody>"
        for (_, dt, sec, desc, qty, gross, ccy, _tt, _tc) in rows:
            body += (f"<tr><td>{dt}</td><td>{sec}</td><td>{desc}</td>"
                     f"<td class='r'>{'' if qty is None else f'{qty:,}'}</td>"
                     f"<td class='r'>{money(gross)}</td><td>{ccy}</td></tr>")
        body += "</tbody></table>"
    else:
        body = "<div class='none'>No transaction activity this period.</div>"

    pages.append(f"""
    <div class="pg">
      <div class="hdr">
        <div class="broker">{BROKER}</div>
        <div class="sub">Investment Account Statement &nbsp;|&nbsp; {MONTHS[m-1]} {FY}</div>
      </div>
      <table class="meta">
        <tr><td class="lbl">Account holder</td><td><b>{CLIENT}</b></td>
            <td class="lbl">Account number</td><td><b>{ACCOUNT}</b></td></tr>
        <tr><td class="lbl">Statement period</td><td>{FY}-{m:02d}-01 to {FY}-{m:02d}-{'31' if m in (1,3,5,7,8,10,12) else ('28' if m==2 else '30')}</td>
            <td class="lbl">Reporting currency</td><td>CAD</td></tr>
        <tr><td class="lbl">Advisor</td><td>K. Lindqvist</td>
            <td class="lbl">Page</td><td>{m} of 12</td></tr>
      </table>
      <h2>Transaction activity</h2>
      {body}
      <div class="foot">
        SYNTHETIC TEST DOCUMENT — generated for AFM 241 Assignment 3. Not a real statement.
        No real client, account or security is represented. Figures are invented.
      </div>
    </div>""")

HTML(string=f"<style>{CSS}</style>" + "".join(pages)).write_pdf(f"{OUT}/statements_FY{FY}.pdf")

# ------------------------------ slips PDF ----------------------------------
slip_css = CSS + """
.slip { border:1.5px solid #1b3a5c; padding:6mm; margin-bottom:8mm; }
.slip h3 { margin:0 0 3mm 0; font-size:11pt; color:#1b3a5c; }
.box { display:flex; gap:6mm; }
.box div { flex:1; border:1px solid #999; padding:3mm; }
.box .lab { font-size:6.6pt; color:#555; text-transform:uppercase; letter-spacing:.5px; }
.box .val { font-size:12pt; font-weight:bold; font-variant-numeric: tabular-nums; }
"""
slip_html = f"""
<style>{slip_css}</style>
<div class="hdr"><div class="broker">Tax slips — {FY}</div>
<div class="sub">{CLIENT} &nbsp;|&nbsp; Account {ACCOUNT}</div></div>

<div class="slip">
  <h3>T5 — Statement of Investment Income</h3>
  <div class="sub">Payer: {BROKER} &nbsp;|&nbsp; Recipient: {CLIENT} &nbsp;|&nbsp; Year: {FY}</div>
  <div class="box" style="margin-top:4mm">
    <div><div class="lab">Box 24 — Actual amount of eligible dividends</div>
         <div class="val">{SLIPS['T5_dividends_actual']:,.2f}</div></div>
    <div><div class="lab">Box 13 — Interest from Canadian sources</div>
         <div class="val">{SLIPS['T5_interest']:,.2f}</div></div>
  </div>
</div>

<div class="slip">
  <h3>T3 — Statement of Trust Income Allocations and Designations</h3>
  <div class="sub">Trust: Halcyon Global Income Fund &nbsp;|&nbsp; Recipient: {CLIENT} &nbsp;|&nbsp; Year: {FY}</div>
  <div class="box" style="margin-top:4mm">
    <div><div class="lab">Total distributions allocated</div>
         <div class="val">{SLIPS['T3_distributions']:,.2f}</div></div>
    <div><div class="lab">Note</div>
         <div style="font-size:8pt">Character of distributions per trust designation; see trust tax
         information sheet. Includes amounts reinvested in units.</div></div>
  </div>
</div>

<div class="foot">SYNTHETIC TEST DOCUMENT — generated for AFM 241 Assignment 3. Not a real tax slip.</div>
"""
HTML(string=slip_html).write_pdf(f"{OUT}/slips_FY{FY}.pdf")

# --------------------------- ground truth ----------------------------------
with open(f"{OUT}/ground_truth.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["month","txn_date","security","description_as_printed","quantity",
                "gross_amount","currency","true_type","must_be_flagged","flag_reason"])
    for (m, dt, sec, desc, qty, gross, ccy, tt, tc) in TXNS:
        w.writerow([m, dt, sec, desc, "" if qty is None else qty, f"{gross:.2f}", ccy,
                    tt, "YES" if tc else "no", tc])

with open(f"{OUT}/opening_cost_base.json", "w") as f:
    json.dump({"account": ACCOUNT, "client": CLIENT, "fiscal_year": FY,
               "reporting_currency": "CAD",
               "positions": [{"security": s, "quantity": q, "cost_base": c,
                              "currency": cc, "note": n} for s, q, c, cc, n in OPENING]}, f, indent=2)

with open(f"{OUT}/slips.json", "w") as f:
    json.dump(SLIPS, f, indent=2)

seeded = sum(1 for t in TXNS if t[8])
print(f"statements: 12 pages, {len(TXNS)} transactions")
print(f"seeded complex cases: {seeded}")
print(f"slip interest {SLIPS['T5_interest']:.2f} vs statements "
      f"{sum(t[5] for t in TXNS if t[7]=='interest'):.2f} -> deliberate variance")
