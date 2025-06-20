<<<<<<< HEAD


from flask import Flask, render_template, request, send_file
import os
import re
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

        branch = self.dep.lower()
        credit_maps = {
            "artificial intelligence": {
            'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3,
            'U20GE101': 3, 'U20GR101': 4, 'U20BS101': 2, 'U20EG103': 2, 'GE3252': 1,
            'U20HS201': 3, 'U20MA201': 4, 'U20PH201': 3, 'U20GE201': 3, 'GE3152': 1,
            'U20CS201': 4, 'U20EC201': 3, 'U20GE203': 2, 'U20GE204': 2, 'U20CS202': 2,
            'U20AI301': 3, 'U20AI302': 3, 'U20AI303': 3, 'U20AI304': 2, 'U20AI305': 2,
            'U20EC306': 4, 'U20MA302': 4,
            'U20AI401': 3, 'U20AI402': 3, 'U20AI403': 3, 'U20AI404': 3,
            'U20AI405': 2, 'U20AI406': 2, 'U20HS202': 3,
            'U20AI501': 4, 'U20AI502': 3, 'U20AI503': 3, 'U20AI504': 2,
            'U20AI505': 2, 'U20AI514': 3, 'U20HS301': 2, 'U20MA501': 4, 'U20OEE52': 2,
            'U20AI601': 3, 'U20AI602': 3, 'U20AI603': 3, 'U20AI604': 3,
            'U20AI605': 2, 'U20AI606': 2, 'U20BA101': 3, 'U20AI525': 3
        },
            "electronics and communication": {
            'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3, 'U20GE101': 3,
            'U20GE102': 4, 'U20BS101': 2, 'U20GE103': 2, 'U20HS201': 3,
            'U20MA201': 4, 'U20PH201': 3, 'U20GE201': 3, 'U20EE201': 3, 'U20EC201': 3,
            'U20GE203': 2, 'U20GE204': 2, 'U20EC202': 2, 'U20MA301': 4, 'U20EC301': 4,
            'U20EC302': 3, 'U20EC303': 3, 'U20EC304': 3, 'U20CS301': 3, 'U20EC305': 2,
            'U20CS302': 2, 'U20MA401': 4, 'U20EC401': 3, 'U20EC402': 3, 'U20EC403': 4,
            'U20HS202': 3, 'U20EC404': 2, 'U20EC405': 2, 'U20EC501': 4, 'U20EC502': 4,
            'U20EC503': 3, 'U20EC504': 3, 'U20EC505': 3, 'U20EC506': 2, 'U20EC507': 2,
            'U20EC601': 4, 'U20EC602': 3, 'U20EC603': 3, 'U20EC604': 3,
            'U20EC605': 2, 'U20EC606': 2, 'U20EC607': 2
        },
            "aeronautical": {
            'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3, 'U20GE101': 3,
            'U20GE102': 4, 'U20BS101': 2, 'U20GE103': 2, 'U20HS201': 3, 'U20MA201': 4,
            'U20PH201': 3, 'U20GE201': 3, 'U20AE201': 3, 'U20AE202': 3, 'U20GE203': 2,
            'U20GE204': 2, 'U20AE203': 2, 'U20MA301': 4, 'U20AE301': 4, 'U20AE302': 3,
            'U20AE303': 3, 'U20AE304': 3, 'U20CS301': 3, 'U20AE305': 2, 'U20CS302': 2,
            'U20MA401': 4, 'U20AE401': 3, 'U20AE402': 3, 'U20AE403': 4, 'U20HS202': 3,
            'U20AE404': 2, 'U20AE405': 2, 'U20AE501': 4, 'U20AE502': 4, 'U20AE503': 3,
            'U20AE504': 3, 'U20AE505': 3, 'U20AE506': 2, 'U20AE507': 2, 'U20AE601': 4,
            'U20AE602': 3, 'U20AE603': 3, 'U20AE604': 3, 'U20AE605': 2, 'U20AE606': 2,
            'U20AE607': 2
        },
            "robotics":  {
            'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3, 'U20GE101': 3,
        'U20GE102': 6, 'U20BS102': 4, 'U20GE103': 4, 'U20HS201': 3, 'U20MA201': 4,
        'U20PH201': 3, 'U20GE201': 3, 'U20ES201': 3, 'U20GE202': 3, 'U20GE203': 4,
        'U20ES202': 4, 'U20GE204': 4, 'U20MA301': 4, 'U20ES303': 3, 'U20RA301': 3,
        'U20RA302': 3, 'U20RA303': 3, 'U20RA304': 3, 'U20RA305': 4, 'U20RA306': 4,
        'U20MA405': 4, 'U20RA401': 3, 'U20ES401': 3, 'U20ES402': 3, 'U20RA402': 4,
        'U20HS202': 3, 'U20RA403': 4, 'U20ES403': 4, 'U20RA501': 3, 'U20RA502': 3,
        'U20ES501': 3, 'U20RA503': 3, 'U20RA504': 3, 'U20RA505': 4, 'U20RA506': 4,
        'U20RA507': 2, 'U20ES601': 3, 'U20BS601': 3, 'U20RA601': 3, 'U20RA602': 3,
        'U20ES602': 4, 'U20RA603': 4, 'U20HS501': 2, 'U20RA701': 3, 'U20RA702': 4,
        'U20RA703': 4, 'U20RA801': 20

        },
            "information technology": {
            'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3, 'U20GE101': 3,
            'U20GE102': 4, 'U20BS101': 2, 'U20GE103': 2, 'U20HS201': 3, 'U20MA201': 4,
            'U20PH201': 3, 'U20GE201': 3, 'U20CS201': 4, 'U20IT201': 3, 'U20GE203': 2,
            'U20GE204': 2, 'U20IT202': 2, 'U20MA301': 4, 'U20IT301': 4, 'U20IT302': 3,
            'U20IT303': 3, 'U20IT304': 3, 'U20IT305': 2, 'U20CS301': 3, 'U20CS302': 2,
            'U20MA401': 4, 'U20IT401': 3, 'U20IT402': 3, 'U20IT403': 4, 'U20HS202': 3,
            'U20IT404': 2, 'U20IT405': 2, 'U20IT501': 3, 'U20IT502': 3, 'U20IT503': 3,
            'U20IT504': 2, 'U20IT505': 2, 'U20IT514': 3, 'U20MA501': 4, 'U20OME52': 2,
            'U20IT601': 3, 'U20IT602': 3, 'U20IT603': 3, 'U20IT604': 3,
            'U20IT605': 2, 'U20IT606': 2, 'U20IT607': 2
        }
        }

        for key in credit_maps:
            if key in branch:
                return self.calculate(credit_maps[key])

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

    text = re.sub(r"[^\x00-\x7F]+", " ", text)

    name_match = re.search(r"Name\s*[:\-]?\s*([A-Z\s\.]+)", text, re.IGNORECASE)
    reg_no_match = re.search(r"Register\s*No\s*[:\-]?\s*(\d+)", text, re.IGNORECASE)
    branch_match = re.search(r"Degree\s*[-–]\s*Branch\s*[:\-]?\s*(.+)", text, re.IGNORECASE)

    if not (name_match and reg_no_match and branch_match):
        raise ValueError("Student name, register number or branch missing.")

    name = name_match.group(1).replace("Date of Birth", "").strip()
    reg_no = reg_no_match.group(1).strip()
    branch = branch_match.group(1).strip()

    pattern = re.compile(
        r"(I{1,3}|IV|V|VI|VII|VIII)\s+"
        r"(U20\w+)\s+"
        r"(.+?)\s+"
        r"(O|A\+|A|B\+|B|C|RA|UA|U)\s+"
        r"(PASS|FAIL|AB)?",
        re.IGNORECASE
    )

    matches = pattern.findall(text)
    if not matches:
        raise ValueError("No subject data found.")

    sem_order = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']
    sem_index = {sem: i for i, sem in enumerate(sem_order)}
    latest_sem = max(matches, key=lambda x: sem_index.get(x[0].upper(), -1))[0].upper()

    subject_data = [
        {"Code": m[1].strip().upper(), "Title": m[2].strip(), "Grade": m[3].strip().upper()}
        for m in matches if m[0].upper() == latest_sem
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

if __name__ == "__main__":
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
=======
from flask import Flask, render_template, request
import os
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import mimetypes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# ---------------- CGPA CALCULATOR ----------------
class CGPA:
    grade_map = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "U": 0}

    def __init__(self, name, reg_no, dep, subject_data):
        self.name = name
        self.reg_no = reg_no
        self.dep = dep
        self.subject_data = subject_data

    def aids(self):
        subject_credits = {
            'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3,
            'U20GE101': 3, 'U20GR101': 4, 'U20BS101': 2, 'U20EG103': 2, 'GE3252': 1,
            'U20HS201': 3, 'U20MA201': 4, 'U20PH201': 3, 'U20GE201': 3, 'GE3152': 1,
            'U20CS201': 4, 'U20EC201': 3, 'U20GE203': 2, 'U20GE204': 2, 'U20CS202': 2,
            'U20AI301': 3, 'U20AI302': 3, 'U20AI303': 3, 'U20AI304': 2, 'U20AI305': 2,
            'U20EC306': 4, 'U20MA302': 4,
            'U20AI401': 3, 'U20AI402': 3, 'U20AI403': 3, 'U20AI404': 3,
            'U20AI405': 2, 'U20AI406': 2, 'U20HS202': 3,
            'U20AI501': 4, 'U20AI502': 3, 'U20AI503': 3, 'U20AI504': 2,
            'U20AI505': 2, 'U20AI514': 3, 'U20HS301': 2, 'U20MA501': 4, 'U20OEE52': 2,
            'U20AI601': 3, 'U20AI602': 3, 'U20AI603': 3, 'U20AI604': 3,
            'U20AI605': 2, 'U20AI606': 2, 'U20BA101': 3, 'U20AI525': 3
        }
        return self.calculate(subject_credits)

    def ece(self):
        subject_credits = {
            'U20HS101': 3, 'U20MA101': 4, 'U20PH101': 3, 'U20CY101': 3, 'U20GE101': 3,
            'U20GE102': 4, 'U20BS101': 2, 'U20GE103': 2, 'U20HS201': 3,
            'U20MA201': 4, 'U20PH201': 3, 'U20GE201': 3, 'U20EE201': 3, 'U20EC201': 3,
            'U20GE203': 2, 'U20GE204': 2, 'U20EC202': 2, 'U20MA301': 4, 'U20EC301': 4,
            'U20EC302': 3, 'U20EC303': 3, 'U20EC304': 3, 'U20CS301': 3, 'U20EC305': 2,
            'U20CS302': 2, 'U20MA401': 4, 'U20EC401': 3, 'U20EC402': 3, 'U20EC403': 4,
            'U20HS202': 3, 'U20EC404': 2, 'U20EC405': 2, 'U20EC501': 4, 'U20EC502': 4,
            'U20EC503': 3, 'U20EC504': 3, 'U20EC505': 3, 'U20EC506': 2, 'U20EC507': 2,
            'U20EC601': 4, 'U20EC602': 3, 'U20EC603': 3, 'U20EC604': 3,
            'U20EC605': 2, 'U20EC606': 2, 'U20EC607': 2
        }
        return self.calculate(subject_credits)

    def calculate(self, subject_credits):
        total_points = 0
        total_credits = 0
        for sub in self.subject_data:
            code = sub['Code'].upper()
            grade = sub['Grade'].upper()
            credit = subject_credits.get(code)
            point = self.grade_map.get(grade)
            if credit is not None and point is not None:
                total_points += credit * point
                total_credits += credit
        return total_points / total_credits if total_credits else 0

# ---------------- TEXT EXTRACTOR ----------------
def extract_student_info(file_path):
    file_type, _ = mimetypes.guess_type(file_path)

    if file_type and file_type.startswith('image'):
        text = pytesseract.image_to_string(Image.open(file_path))
    elif file_type == 'application/pdf':
        doc = fitz.open(file_path)
        text = "".join([page.get_text() for page in doc])
    else:
        raise ValueError("Unsupported file type")

    clean_text = re.sub(r"[^\x00-\x7F]+", " ", text)

    # Debug output (optional)
    with open("debug_output.txt", "w", encoding="utf-8") as f:
        f.write(clean_text)

    # Extract Register Number with fallback
    reg_no_match = re.search(r"Register\s*No\s*[:\-]?\s*(\d{6,})", clean_text, re.IGNORECASE)
    if not reg_no_match:
        reg_no_match = re.search(r"Register\s*No\s*[:\-]?\s*(\d{6,})\s+Name", clean_text, re.IGNORECASE)
    if not reg_no_match:
        raise ValueError("Register number not found. Check format.")
    register_no = reg_no_match.group(1).strip()

    # Extract Name (handle '5' -> 'S')
    name_match = re.search(r"Name\s*[:\-]?\s*([A-Z\s\.5]+)", clean_text, re.IGNORECASE)
    if not name_match:
        raise ValueError("Name not found. Check format.")
    name = name_match.group(1).replace("5", "S").strip()

    # Extract Branch
    branch_match = re.search(r"Degree\s*[-–]\s*Branch\s*[:\-]?\s*(.+?)(?:\n|$)", clean_text, re.IGNORECASE)
    if not branch_match:
        raise ValueError("Degree - Branch not found. Check format.")
    degree_branch = branch_match.group(1).strip()

    # Extract subjects
    pattern = re.compile(r"(U20\w+|GE\d+)\s+(.+?)\s+([A-Z\+]{1,2})\s+PASS", re.IGNORECASE)
    subject_data = []
    for match in pattern.findall(clean_text):
        code, title, grade = match
        subject_data.append({
            'Semester': 'UNKNOWN',
            'Code': code.strip().upper(),
            'Title': title.strip(),
            'Grade': grade.strip().upper()
        })

    return name, register_no, degree_branch, subject_data

# ---------------- ROUTES ----------------
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

        if "Artificial Intelligence" in dep:
            cgpa = student.aids()
        elif "Electronics and Communication" in dep:
            cgpa = student.ece()
        else:
            return f"Branch '{dep}' not supported."

        result = f"""
        Name: {name}<br>
        Reg No: {reg_no}<br>
        Branch: {dep}<br>
        <strong>CGPA: {cgpa:.2f}</strong>
        """
    except Exception as e:
        result = f"Error processing file: {e}"

    return result

# ---------------- RUN ----------------
if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
>>>>>>> 2d6f937 (Initial commit)
