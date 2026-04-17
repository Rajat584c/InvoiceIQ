"""
tests/test_ocr.py
Unit tests for InvoiceIQ W1 OCR pipeline.
Run with: pytest tests/test_ocr.py -v
"""

import pytest
from engine.ocr import extract_fields, _clean_amount, _detect_transaction_type


# ---------------------------------------------------------------------------
# Synthetic invoice texts (no real PDF needed for unit tests)
# ---------------------------------------------------------------------------

INTRA_STATE_INVOICE = """
INVOICE
Invoice No: INV-2024-001
Invoice Date: 15/04/2024

Supplier GSTIN: 27AAPFU0939F1ZV
Buyer GSTIN: 27BBCDE1234F1ZK

Place of Supply: Maharashtra

HSN Code: 8471

Description                     Amount
Laptop computers                Rs. 50,000.00

Taxable Amount:                 Rs. 50,000.00
CGST @ 9%:                      Rs. 4,500.00
SGST @ 9%:                      Rs. 4,500.00
Grand Total:                    Rs. 59,000.00
"""

INTER_STATE_INVOICE = """
TAX INVOICE

Invoice Number: GST/2024/0042
Date: 20-03-2024

Our GSTIN: 06AAHCR1234A1Z5     (Haryana)
Customer GSTIN: 29ABCDE5678F1ZP  (Karnataka)

Place of Supply: Karnataka

HSN/SAC: 9983

Taxable Value:                  INR 1,00,000.00
IGST @ 18%:                     INR 18,000.00
Total Amount Payable:           INR 1,18,000.00
"""

AMBIGUOUS_INVOICE = """
Bill
Date: 01/01/2024
Total: Rs. 5000
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCleanAmount:
    def test_with_commas(self):
        assert _clean_amount("1,00,000.00") == 100000.0

    def test_plain_number(self):
        assert _clean_amount("59000") == 59000.0

    def test_empty_string(self):
        assert _clean_amount("") is None

    def test_none_input(self):
        assert _clean_amount(None) is None


class TestIntraStateInvoice:
    def setup_method(self):
        self.fields = extract_fields(INTRA_STATE_INVOICE, "test_intra.pdf")

    def test_invoice_number(self):
        assert self.fields["invoice_number"] == "INV-2024-001"

    def test_gstin_supplier(self):
        assert self.fields["gstin_supplier"] == "27AAPFU0939F1ZV"

    def test_gstin_buyer(self):
        assert self.fields["gstin_buyer"] == "27BBCDE1234F1ZK"

    def test_cgst_amount(self):
        assert self.fields["cgst_amount"] == 4500.0

    def test_sgst_amount(self):
        assert self.fields["sgst_amount"] == 4500.0

    def test_total_amount(self):
        assert self.fields["total_amount"] == 59000.0

    def test_transaction_type_intra(self):
        assert self.fields["transaction_type"] == "intra-state"

    def test_total_tax_calculation(self):
        assert self.fields["total_tax"] == 9000.0

    def test_hsn_code(self):
        assert self.fields["hsn_code"] == "8471"


class TestInterStateInvoice:
    def setup_method(self):
        self.fields = extract_fields(INTER_STATE_INVOICE, "test_inter.pdf")

    def test_igst_amount(self):
        assert self.fields["igst_amount"] == 18000.0

    def test_igst_rate(self):
        assert self.fields["igst_rate"] == 18.0

    def test_transaction_type_inter(self):
        assert self.fields["transaction_type"] == "inter-state"

    def test_total_amount(self):
        assert self.fields["total_amount"] == 118000.0


class TestAmbiguousInvoice:
    def setup_method(self):
        self.fields = extract_fields(AMBIGUOUS_INVOICE, "test_ambiguous.pdf")

    def test_transaction_type_unknown(self):
        assert self.fields["transaction_type"] == "unknown"

    def test_missing_gstin_is_none(self):
        assert self.fields["gstin_supplier"] is None
        assert self.fields["gstin_buyer"] is None