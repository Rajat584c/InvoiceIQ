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
| PDF Invoice OCR & Field Extraction | pdfplumber, pytesseract | ✅ |
| GST Reconciliation Engine (CGST/SGST/IGST) | Pandas, Regex | 🚧 |
| Duplicate & Anomaly Detection | Isolation Forest, FuzzyWuzzy | ⏳ |
| Interactive Dashboard | Streamlit | ⏳ |

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
```

---

## 🗂️ Project Structure
```
InvoiceIQ/
├── app/
│   └── streamlit_app.py       
├── engine/
│   ├── ocr.py                 
│   ├── gst_reconciler.py      
│   └── anomaly_detector.py    
├── data/
│   └── generate_sample_invoices.py      
├── tests/
│   └── test_ocr.py
├── requirements.txt
├── README.md
└── .gitignore
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
