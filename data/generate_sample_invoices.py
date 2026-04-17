"""
data/generate_sample_invoices.py
Generates realistic sample Indian GST invoice PDFs for testing the OCR pipeline.
Run once: python data/generate_sample_invoices.py
Requires: pip install fpdf2
"""

from fpdf import FPDF
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "sample_invoices"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def make_invoice(filename: str, data: dict):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    # Header
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "TAX INVOICE", align="C", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, data["supplier_name"], align="C", ln=True)
    pdf.cell(0, 6, data["supplier_address"], align="C", ln=True)
    pdf.ln(4)

    # Invoice meta
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 7, f"Invoice No: {data['invoice_no']}")
    pdf.cell(0, 7, f"Invoice Date: {data['invoice_date']}", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 7, f"Supplier GSTIN: {data['gstin_supplier']}")
    pdf.cell(0, 7, f"Buyer GSTIN: {data['gstin_buyer']}", ln=True)
    pdf.cell(0, 7, f"Place of Supply: {data['place_of_supply']}", ln=True)
    pdf.ln(4)

    # Line items header
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(80, 8, "Description", border=1, fill=True)
    pdf.cell(30, 8, "HSN", border=1, fill=True)
    pdf.cell(40, 8, "Qty", border=1, fill=True)
    pdf.cell(40, 8, "Amount (INR)", border=1, fill=True, ln=True)

    pdf.set_font("Helvetica", "", 10)
    for item in data["items"]:
        pdf.cell(80, 8, item["desc"], border=1)
        pdf.cell(30, 8, item["hsn"], border=1)
        pdf.cell(40, 8, str(item["qty"]), border=1)
        pdf.cell(40, 8, f"{item['amount']:,.2f}", border=1, ln=True)

    pdf.ln(4)

    # Tax summary
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(150, 7, "Taxable Amount:")
    pdf.cell(0, 7, f"Rs. {data['taxable_amount']:,.2f}", ln=True)

    if data.get("cgst_amount"):
        pdf.cell(150, 7, f"CGST @ {data['cgst_rate']}%:")
        pdf.cell(0, 7, f"Rs. {data['cgst_amount']:,.2f}", ln=True)
        pdf.cell(150, 7, f"SGST @ {data['sgst_rate']}%:")
        pdf.cell(0, 7, f"Rs. {data['sgst_amount']:,.2f}", ln=True)

    if data.get("igst_amount"):
        pdf.cell(150, 7, f"IGST @ {data['igst_rate']}%:")
        pdf.cell(0, 7, f"Rs. {data['igst_amount']:,.2f}", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(150, 8, "Grand Total:")
    pdf.cell(0, 8, f"Rs. {data['total_amount']:,.2f}", ln=True)

    pdf.output(str(OUTPUT_DIR / filename))
    print(f"Created: {filename}")


# ---------------------------------------------------------------------------
# Sample invoices
# ---------------------------------------------------------------------------

SAMPLES = [
    {
        "filename": "intra_state_invoice_001.pdf",
        "data": {
            "supplier_name": "Tech Solutions Pvt Ltd",
            "supplier_address": "Andheri East, Mumbai, Maharashtra - 400069",
            "invoice_no": "INV-2024-001",
            "invoice_date": "15/04/2024",
            "gstin_supplier": "27AAPFU0939F1ZV",
            "gstin_buyer": "27BBCDE1234F1ZK",
            "place_of_supply": "Maharashtra",
            "items": [
                {"desc": "Laptop Computer", "hsn": "8471", "qty": 2, "amount": 50000},
            ],
            "taxable_amount": 50000.00,
            "cgst_rate": 9, "cgst_amount": 4500.00,
            "sgst_rate": 9, "sgst_amount": 4500.00,
            "total_amount": 59000.00,
        },
    },
    {
        "filename": "inter_state_invoice_002.pdf",
        "data": {
            "supplier_name": "Global Traders",
            "supplier_address": "Sector 14, Gurugram, Haryana - 122001",
            "invoice_no": "GST/2024/0042",
            "invoice_date": "20/03/2024",
            "gstin_supplier": "06AAHCR1234A1Z5",
            "gstin_buyer": "29ABCDE5678F1ZP",
            "place_of_supply": "Karnataka",
            "items": [
                {"desc": "Consulting Services", "hsn": "9983", "qty": 1, "amount": 100000},
            ],
            "taxable_amount": 100000.00,
            "igst_rate": 18, "igst_amount": 18000.00,
            "total_amount": 118000.00,
        },
    },
    {
        "filename": "intra_state_invoice_003.pdf",
        "data": {
            "supplier_name": "Office Supplies Co",
            "supplier_address": "T Nagar, Chennai, Tamil Nadu - 600017",
            "invoice_no": "OS/TN/2024/089",
            "invoice_date": "01/05/2024",
            "gstin_supplier": "33AABCO1234C1ZM",
            "gstin_buyer": "33XYZCO5678D1ZA",
            "place_of_supply": "Tamil Nadu",
            "items": [
                {"desc": "Office Chair", "hsn": "9401", "qty": 5, "amount": 12500},
                {"desc": "Office Desk",  "hsn": "9403", "qty": 2, "amount": 18000},
            ],
            "taxable_amount": 30500.00,
            "cgst_rate": 9, "cgst_amount": 2745.00,
            "sgst_rate": 9, "sgst_amount": 2745.00,
            "total_amount": 35990.00,
        },
    },
]

if __name__ == "__main__":
    for s in SAMPLES:
        make_invoice(s["filename"], s["data"])
    print(f"\nAll sample invoices saved to: {OUTPUT_DIR}")
    print("Now run: python -c \"from engine.ocr import process_invoice_folder; import pandas as pd; df = process_invoice_folder('data/sample_invoices'); print(df.to_string())\"")