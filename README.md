# 🎓 CGPA Calculator – DSEC (Autonomous)

A web application designed specifically for students of **Dhanalakshmi Srinivasan Engineering College (Autonomous), Perambalur** to accurately calculate their CGPA based on uploaded result PDFs/images.

---

## 🏫 About

This CGPA Calculator is **custom-built for DSEC (A)**, Perambalur. It extracts and processes students' academic results semester-wise using OCR and PDF parsing techniques, matches subject credits with the respective department, and computes the CGPA. If any subject is failed (RA/U/UA), CGPA calculation is restricted as per academic regulations.

---

## ✅ Features

- 📎 **Supports PDF & Image Uploads**  
  Compatible with Anna University format mark statements from DSEC.

- 🧠 **Automated Data Extraction**  
  Uses OCR and parsing to detect:
  - Name, Register Number, Branch
  - Subject Code, Title, Grade, Semester, Result

- 🚫 **Fail/Absent Handling**  
  If a student has failed or is absent in any subject, CGPA is **not calculated**.

- 🧮 **Department-Specific CGPA Logic**  
  Credit mapping is predefined for branches like IT, AI&DS, ECE, etc., based on DSEC regulations.

- 🧾 **Downloadable PDF Report**  
  Generates a clean, structured CGPA report for printing or record.

---

## 🛠 Technologies

- `Python 3.10`
- `Flask` – Web framework
- `PyMuPDF` – PDF extraction
- `Pytesseract` – OCR (for scanned images)
- `ReportLab` – PDF generation
- `Jinja2` – Templating for HTML

---

## 🚀 Usage Instructions

### 🔧 Local Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/cgpa-calculator.git
cd cgpa-calculator

# Optional: Create a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
