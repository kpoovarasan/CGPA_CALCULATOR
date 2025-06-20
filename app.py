from flask import Flask, render_template, request, send_file
import os
import re
import difflib
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import mimetypes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

class CGPA:
    grade_map = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "U": 0, "RA": 0, "UA": 0}

    def __init__(self, name, reg_no, dep, subject_data):
        self.name = name
        self.reg_no = reg_no
        self.dep = dep
        self.subject_data = subject_data

    def has_fail_or_absent(self):
        for sub in self.subject_data:
            if sub['Grade'].upper() in ['U', 'RA', 'UA']:
                return True
        return False

    def calculate(self, subject_credits):
        total_points = 0
        total_credits = 0
        for sub in self.subject_data:
            code = sub['Code'].upper()
            grade = sub['Grade'].upper()
            credit = subject_credits.get(code, 3)  # default to 3
            point = self.grade_map.get(grade)
            if point is not None:
                total_points += credit * point
                total_credits += credit
        return total_points / total_credits if total_credits else 0

    def get_cgpa(self):
        if self.has_fail_or_absent():
            return None

        branch_input = self.dep.lower()
        credit_maps = {
            "artificial intelligence": {
            'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3,
            'U20GE101': 3, 'U20GR101': 4, 'U20BS101': 2, 'U20EG103': 2, 'GE3252': 1,
            'U20HS201': 3, 'U20MA201': 4, 'U20PH201': 3, 'U20GE201': 3, 'GE3152': 1,
            'U20CS201': 3, 'U20EC201': 3, 'U20GE203': 2, 'U20GE204': 2, 'U20CS202': 2,
            'U20AI301': 3, 'U20AI302': 3, 'U20AI303': 3, 'U20AI304': 2, 'U20AI305': 2,
            'U20EC306': 4, 'U20MA302': 4,
            'U20AI401': 3, 'U20AI402': 3, 'U20AI403': 3, 'U20AI404': 3,
            'U20AI405': 2, 'U20AI406': 2, 'U20HS202': 3,
            'U20AI501': 4, 'U20AI502': 3, 'U20AI503': 3, 'U20AI504': 2,
            'U20AI505': 2, 'U20AI514': 3, 'U20HS301': 2, 'U20MA501': 4, 'U20OEE52': 2,
            'U20AI601': 3, 'U20AI602': 3, 'U20AI603': 3, 'U20AI604': 3,
            'U20AI605': 2, 'U20AI606': 2, 'U20BA101': 3, 'U20AI525': 3,'U20AI701': 3,
            'U20AI702': 3,'U20AI703': 4,'U20AI704': 3,'U20AI705': 2,'U20AI706': 2,
            
        },
            "electronics and communication": {
            'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3, 'U20GE101': 3,
            'U20GE102': 4, 'U20BS101': 2, 'U20GE103': 2, 'U20HS201': 3,
            'U20MA201': 4, 'U20PH201': 3, 'U20GE201': 3, 'U20EE201': 3, 'U20EC201': 3,
            'U20GE203': 2, 'U20GE204': 2, 'U20EC202': 2, 'U20MA301': 4, 'U20EC301': 4,
            'U20EC302': 3, 'U20EC303': 3, 'U20EC304': 3, 'U20CS301': 3, 'U20EC305': 2,
            'U20CS302': 2,'U20HS301': 1, 'U20MA401': 4, 'U20EC401': 3, 'U20EC402': 3, 'U20EC403': 4,
            'U20HS202': 3, 'U20EC404': 2, 'U20EC405': 2, 'U20EC501': 4, 'U20EC502': 4,
            'U20EC503': 3, 'U20EC504': 3, 'U20EC505': 3, 'U20EC506': 2, 'U20EC507': 2,
            'U20EC601': 4, 'U20EC602': 3, 'U20EC603': 3, 'U20EC604': 3,
            'U20EC605': 2, 'U20EC606': 2, 'U20EC607': 2,'GE3252': 1,'GE3152': 1,
            'U20EC701': 4,'U20EC702': 3,'U20EC703': 3,'U20EC704': 3,'U20EC705': 2,'U20EC706': 1,
            'U20EC801': 6
        },
            "aeronautical": {
            'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3, 'U20GE101': 3,'U20GE102': 4, 'U20BS101': 2, 'U20GE103': 2, 
            'U20HS201': 3, 'U20MA201': 4, 'U20PH201': 3, 'U20GE201': 3, 'U20AE201': 3, 'U20AE202': 3, 'U20GE203': 2,'U20GE204': 2, 'U20AE203': 2,
            'U20MA301': 4, 'U20AE301': 3, 'U20AE302': 3,'U20AE303': 3, 'U20HS202': 3, 'U20ES301': 3, 'U20ES302': 2, 'U20AE304': 2,
            'U20MA401': 4, 'U20AE401': 3, 'U20AE402': 3, 'U20AE403': 3, 'U20AE404': 4,'U20AE405': 3, 'U20AE406': 2, 'U20AE407': 2,
            'U20AE501': 3, 'U20AE502': 4, 'U20AE503': 3,'U20AE504': 3, 'U20AE505': 3, 'U20AE506': 2, 'U20AE507': 1, 
            'U20AE601': 4,  'U20AE602': 3, 'U20AE603': 3, 'U20AE604': 3, 'U20AE605': 2, 'U20AE606': 2, 'U20HS501': 1,
            'U20AE701': 3,  'U20AE702': 3, 'U20AE703': 2, 'U20AE704': 2,'U20HS701': 3,'U20AE801': 6,
            'U23HST11': 3, 'U23MAT12': 4, 'U23PHT13': 3, 'U23CYT14': 3, 'U23GET16': 4,'GE3152': 1,  'U23BSP11': 2, 'U23HSP12': 1, 'U23GEP14': 2,
            'U23HST21': 2,'U23MAT22': 4, 'U23GET15': 3, 'U23PHT23': 3, 'U23EET26': 3, 'GE3252': 1,'U23EEP25': 2, 'U23HSP22': 2, 'U23GEP13': 2, 
            'U23MAT31': 4, 'U23AET31': 3, 'U23AET32': 4, 'U23MET32': 3, 'U23AET34': 3, 'U23GET41': 2, 'U23AEP31': 2,'U23AEP32': 2,
            'U23MAT41': 4, 'U23AET41': 3, 'U23AET42': 3, 'U23AET43': 3,'U23AET44': 3, 'U23AET45': 3, 'U23AEP41': 2, 'U23AEP42': 2, 'U23AEP43': 2,
            'U23AET51': 3, 'U23AET52': 3, 'U23AET53': 3, 'U23AET54': 3, 'U23AET55': 3, 'U23AEP51': 2, 'U23AEP52': 2, 
            'U23AET61': 3, 'U23AET62': 3, 'U23AET63': 3, 'U23AEP61': 2, 'U23AEP62': 2, 
            'U23GET72': 3, 'U23AET72': 3, 'U23AET73': 3, 'U23AEP71': 2, 'U23AEP72': 2, 
            'U23AEP81': 8
        },
            "robotics":  {
            'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3, 'U20GE101': 3,'U20GE102': 4, 'U20BS102': 2, 'U20GE103': 2, 
            'U20HS201': 3, 'U20MA201': 4,'U20PH201': 3, 'U20GE201': 3, 'U20ES201': 3, 'U20GE202': 3, 'U20GE203': 2,'U20ES202': 2, 'U20GE204': 2,
            'U20MA301': 4, 'U20ES303': 3, 'U20RA301': 3, 'U20RA302': 3, 'U20RA303': 3, 'U20RA304': 3, 'U20RA305': 2, 'U20RA306': 2,
            'U20MA405': 4, 'U20RA401': 3, 'U20ES401': 3, 'U20ES402': 3, 'U20RA402': 4, 'U20HS202': 3, 'U20RA403': 2, 'U20ES403': 2,
            'U20RA501': 3, 'U20RA502': 3,'U20ES501': 3, 'U20RA503': 3, 'U20RA504': 3, 'U20RA505': 2, 'U20RA506': 2,'U20RA507': 1,
            'U20ES601': 3, 'U20BS601': 3, 'U20RA601': 3, 'U20RA602': 3,'U20ES602': 2, 'U20RA603': 2, 'U20HS501': 1,
            'U20RA701': 3, 'U20RA702': 2,'U20RA703': 2, 
            'U20RA801': 20,'GE3252': 1,'GE3152': 1

        },
            "information technology": {
            'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3, 'U20GE101': 3,'U20GE102': 4, 'U20BS101': 2, 'U20GE103': 2, 
            'U20HS201': 3, 'U20MA201': 4,
            'U20PH201': 3, 'U20GE201': 3, 'U20CS201': 4, 'U20EC201': 3, 'U20GE203': 2,'U20GE204': 2, 'U20CS202': 2,
            'U20MA301': 4,  'U20IT302': 3,'U20EC301': 4, 'U20IT303': 3, 'U20IT304': 3, 'U20IT305': 3, 'U20IT306': 2, 'U20IT307': 2,
            'U20IT401': 3, 'U20IT402': 3, 'U20IT403': 3,'U20IT404': 3, 'U20HS202': 3, 'U20EC401': 3,'U20IT406': 2, 'U20IT405': 2, 
            'U20MA501': 4,'U20IT501': 3, 'U20IT502': 3, 'U20IT503': 3,'U20IT504': 2, 'U20IT505': 2,
            'U20IT601': 3, 'U20IT602': 3, 'U20IT603': 3, 'U20IT604': 3,'U20IT605': 2, 'U20IT606': 2,'U20HS601': 1,
            'U20IT701': 3, 'U20IT702': 3, 'U20IT703': 3, 'U20IT704': 2,'U20IT705': 1, 
            'U20IT801': 6,'GE3252': 1,'GE3152': 1
        },
            "aerospace": {
                'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3, 'U20GE101': 3, 'U20GE102': 4, 'U20BS101': 2, 'U20GE103': 2, 
                'U20HS201': 3, 'U20MA201': 4,'U20PH201': 3, 'U20GE201': 3, 'U20ES201': 3, 'U20GE202': 3, 'U20GE203': 2,'U20ES202': 2, 'U20GE204': 2,
                'U20MA301': 4, 'U20AE301': 3, 'U20ES301': 3,'U20AE302': 3, 'U20AS302': 3, 'U20AS303': 3, 'U20ES302': 2, 'U20AE304': 2,
                'U20MA402': 4, 'U20AS401': 3, 'U20AS402': 3, 'U20AE405': 3, 'U20AS404': 3,'U20HS202': 3, 'U20AS405': 2, 'U20AS406': 2,
                'U20AE501': 3, 'U20AS501': 3,  'U20AS502': 3, 'U20AS503': 3, 'U20AS504': 3, 'U20AS505': 2, 'U20AS506': 2, 'U20HS501': 1, 
                'U20AS601': 3, 'U20AE602': 3, 'U20AE601': 3, 'U20AS603': 3, 'U20AE701': 3, 'U20AS605': 2, 'U20AS606': 2, 'U20AS607': 2,
                'U20AS701': 3,'U20AS702': 3, 'U20AS703': 3, 'U20AS704': 2, 'U20AS705': 1, 
                'U20AS801': 6,'GE3252': 1,'GE3152': 1
            },
            "biotechnology": {
                'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3, 'U20GE101': 3, 'U20GE102': 4, 'U20BS101': 2, 'U20GE103': 2, 
                'U20HS201': 3, 'U20MA201': 4,'U20PH201': 3, 'U20GE201': 3, 'U20BT201': 3, 'U20BT202': 3, 'U20GE203': 2,'U20BT203': 2, 'U20GE204': 2,
                'U20MA301': 4, 'U20BT301': 4, 'U20BT302': 3,'U20BT303': 3, 'U20BT304': 3, 'U20BT305': 3, 'U20BT306': 2, 'U20BT307': 2,
                'U20MA404': 4, 'U20BT401': 3, 'U20BT402': 3, 'U20BT403': 3, 'U20BT404': 3,'U20HS202': 3, 'U20BT405': 2, 'U20BT406': 2, 
                'U20BT501': 3, 'U20BT502': 3,'U20BT503': 3, 'U20BT504': 4, 'U20HS501': 1, 'U20BT505': 2, 'U20BT506': 2,
                'U20BT601': 3, 'U20BT602': 4, 'U20BT603': 3, 'U20BT604': 3, 'U20BT605': 2,'U20BT606': 2, 
                'U20HS701': 3, 'U20BT701': 3, 'U20BT702': 3, 'U20BT703': 2,'U20BT704': 1, 
                'U20BT801': 3, 'U20BT802': 6,'GE3252': 1,'GE3152': 1
            }
        }
        for key in credit_maps:
            if key in branch_input:
                return self.calculate(credit_maps[key])

        # Try fuzzy match on cleaned input
        # Extract only the meaningful part
        cleaned_branch = re.sub(r"[^a-z\s]", "", branch_input)  # remove punctuation
        cleaned_branch = re.sub(r"\s+", " ", cleaned_branch).strip()
    
        # Try fuzzy match
        closest = difflib.get_close_matches(cleaned_branch, credit_maps.keys(), n=1, cutoff=0.6)
        if closest:
            return self.calculate(credit_maps[closest[0]])
    
        raise ValueError(f"Branch '{self.dep}' not supported.")

def extract_student_info(filepath):
    
    file_type, _ = mimetypes.guess_type(filepath)
    if file_type.startswith("image"):
        text = pytesseract.image_to_string(Image.open(filepath))
    elif file_type == "application/pdf":
        doc = fitz.open(filepath)
        text = "".join([page.get_text() for page in doc])
    else:
        raise ValueError("Unsupported file type")

    # Clean text
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # remove non-ASCII
    text = re.sub(r"\s+", " ", text)  # normalize whitespace

    # Extract name
    name_match = re.search(r"Name\s*[:\-]?\s*([A-Z\s\.]+?)\s*(Register|Date|DOB|Reg)", text, re.IGNORECASE)
    reg_no_match = re.search(r"Register\s*No\s*[:\-]?\s*(\d+)", text, re.IGNORECASE)

    # Improved branch regex that captures even broken OCR words
    branch_match = re.search(
    r"Degree\s*[-–]?\s*Branch\s*[:\-]?\s*(?:B\.?Tech\.?|B\.?E\.?)?\s*[-–]?\s*([A-Za-z\s&\.\-]+?)(?=\s{2,}|\sSEMESTER|\sSUB-CODE)",
    text, re.IGNORECASE
)


    if not (name_match and reg_no_match and branch_match):
        raise ValueError("Student name, register number or branch missing.")

    name = name_match.group(1).strip()
    reg_no = reg_no_match.group(1).strip()

    # Group(2) captures department even if there's noise
    branch = branch_match.group(1).strip()
    branch = re.sub(r"\s+", " ", branch)  # normalize spaces

    # Subject pattern: SEM CODE TITLE GRADE RESULT
    pattern = re.compile(
        r"(I{1,3}|IV|V|VI|VII|VIII)\s+"
        r"(U\d{2}\w+)\s+"
        r"([A-Za-z0-9\s\.\,\-\(\)\/&]+?)\s+"
        r"(O|A\+|A|B\+|B|C|U|RA|UA)\s+"
        r"(PASS|FAIL|AB)",
        re.IGNORECASE
    )

    matches = pattern.findall(text)
    if not matches:
        raise ValueError("No subject data found.")

    subject_data = [
        {
            "Semester": m[0].strip().upper(),
            "Code": m[1].strip().upper(),
            "Title": m[2].strip(),
            "Grade": m[3].strip().upper(),
            "Result": m[4].strip().upper()
        }
        for m in matches
    ]

    return name, reg_no, branch, subject_data


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    if 'result_pdf' not in request.files:
        return "No file uploaded"

    file = request.files['result_pdf']
    if file.filename == '':
        return "No selected file"

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    try:
        name, reg_no, dep, subject_data = extract_student_info(filepath)
        student = CGPA(name, reg_no, dep, subject_data)

        if student.has_fail_or_absent():
            return render_template('result.html', error="CGPA cannot be calculated due to failed or absent subjects.", name=name, reg_no=reg_no, dep=dep, subject_data=subject_data)

        cgpa = student.get_cgpa()
        if cgpa is None:
            return render_template('result.html', error="Branch not supported or invalid CGPA.", name=name, reg_no=reg_no, dep=dep, subject_data=subject_data)

        return render_template('result.html', name=name, reg_no=reg_no, dep=dep, cgpa=round(cgpa, 2), subject_data=subject_data)

    except Exception as e:
        return render_template('result.html', error=str(e))
@app.route('/download', methods=['POST'])
def download():
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib.units import inch

    name = request.form['name']
    reg_no = request.form['reg_no']
    dep = request.form['dep']
    cgpa = request.form['cgpa']

    # Collect subject data
    subject_data = []
    for key in request.form:
        if key.startswith('subject_'):
            _, idx, field = key.split('_')
            idx = int(idx)
            while len(subject_data) <= idx:
                subject_data.append({'Semester': '', 'Code': '', 'Title': '', 'Grade': '', 'Result': ''})
            subject_data[idx][field] = request.form[key]

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Draw Logos
    logo_left = "static/dsec_logo.jpg"
    logo_right = "static/dsec_ayya_logo.jpg"
    if os.path.exists(logo_left):
        c.drawImage(logo_left, 50, height - 100, width=60, height=60)
    if os.path.exists(logo_right):
        c.drawImage(logo_right, width - 110, height - 100, width=60, height=60)

    # Header Text
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 60, "Dhanalakshmi Srinivasan Engineering College (A)")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 75, "(Approved by AICTE & Affiliated to Anna University, Chennai)")
    c.drawCentredString(width / 2, height - 88, "Accredited with 'A' Grade by NAAC, Accredited by TCS")
    c.drawCentredString(width / 2, height - 101, "Accredited by NBA with BME, ECE & EEE")
    c.drawCentredString(width / 2, height - 114, "Perambalur - 621212, Tamil Nadu")

    y = height - 140
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Name: {name}")
    c.drawString(320, y, f"Reg No: {reg_no}")
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Department: {dep}")
    y -= 20
    c.drawString(50, y, f"CGPA: {cgpa}")
    y -= 30

    # Table Data
    data = [["Semester", "Subject Code", "Title of Paper", "Grade", "Result"]]
    for subject in subject_data:
        data.append([
            subject.get("Semester", ""),
            subject.get("Code", ""),
            subject.get("Title", "")[:45],  # Optional: truncate if needed
            subject.get("Grade", ""),
            subject.get("Result", "")
        ])

    table = Table(data, colWidths=[60, 80, 220, 50, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
    ]))

    # Estimate and fit table height
    table.wrapOn(c, width, height)
    table_height = 18 * len(data)
    table_y = y - table_height

    # Start table on a new page if necessary
    if table_y < 40:
        c.showPage()
        y = height - 60
        table_y = y - table_height

    table.drawOn(c, 50, table_y)

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="CGPA_Result.pdf", mimetype='application/pdf')



if __name__ == "__main__":
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
