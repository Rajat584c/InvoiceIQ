# 🧾 InvoiceIQ — AI-Powered Invoice Intelligence for Indian SMEs

> Automates GST reconciliation and flags payment anomalies from raw PDF invoices.
> Built for Indian micro-businesses handling CGST/SGST/IGST compliance.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active--Development-orange)

---

## 🚀 Live Demo
👉 [Launch App on Streamlit Cloud](link-inprogress)  
*(Upload any Indian GST invoice PDF to try it)*

---

## 🎯 Problem It Solves

Indian micro-SMEs process hundreds of invoices monthly but:
- Manually check GST calculations (error-prone)
- Miss duplicate payments
- Have no system to flag suspicious vendors

**InvoiceIQ automates all three in under 10 seconds per invoice.**

---

## ⚙️ Features

| Feature | Tech Used | Status |
|---|---|---|
| PDF Invoice OCR & Field Extraction | pdfplumber, pytesseract, fpdf2 | ✅ Week 1 |
| GST Reconciliation Engine (CGST/SGST/IGST) | Pandas, Regex | 🚧 Week 2 |
| Duplicate & Anomaly Detection | Isolation Forest, thefuzz | ⏳ Week 3 |
| Interactive Dashboard | Streamlit | ⏳ Week 4 |

---

## 🏗️ Architecture
```
PDF Invoice
↓
OCR Pipeline (pdfplumber + pytesseract)
↓
Structured DataFrame (invoice_no, gstin, amounts, tax)
↓
GST Rule Engine → ✅ Valid / ❌ Mismatch
↓
ML Anomaly Detector → Risk Score (0–100)
↓
Streamlit Dashboard → Alerts + Export
```
---

## 📦 Quickstart

```bash
git clone https://github.com/Rajat584c/InvoiceIQ.git
cd InvoiceIQ
pip install -r requirements.txt
streamlit run app.py

# Generate sample invoices + run tests
python data/generate_sample_invoices.py
pytest tests/ -v
```

---

## 🗂️ Project Structure
```
InvoiceIQ/
├── app/
│   └── streamlit_app.py            # ⏳ W4: Interactive dashboard (Streamlit)
├── engine/
│   ├── __init__.py                 # Makes 'engine' a Python package
│   ├── ocr.py                      # ✅ W1: PDF/Image → structured DataFrame
│   ├── gst_reconciler.py           # ⏳ W2: CGST/SGST/IGST validation rules
│   └── anomaly_detector.py         # ⏳ W3: Isolation Forest + fuzzy matching
├── data/
│   ├── generate_sample_invoices.py # ✅ W1: Synthetic GST invoice generator
│   └── sample_invoices/            # Generated test PDFs (gitkeep only)
├── tests/
│   ├── __init__.py
│   └── test_ocr.py                 # ✅ W1: 19 unit tests (all passing)
├── .gitignore
├── LICENSE                         # MIT
├── README.md
└── requirements.txt
```
---

## 📊 Sample Output

*(Will be adding a screenshot of my Streamlit dashboard here in Week 4)*

---

## 🧠 Key Technical Decisions

- **pdfplumber over PyPDF2**: better table and coordinate-based text extraction for structured invoices
- **Isolation Forest**: unsupervised, no labeled fraud data needed (realistic for SME context)
- **Rule-based GST first, ML second**: hybrid approach catches both known errors and unknown patterns

---

## 👤 Author

**Rajat Kumar Jena**  
PGDM Big Data Analytics | FORE School of Management, New Delhi 
| [LinkedIn](https://www.linkedin.com/in/rajat-kumar-jena-3009a41b5/) | Email:rj584c@gmail.com
