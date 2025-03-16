from flask import Flask, request, jsonify, render_template
import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import re
import os

app = Flask(__name__)

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

# Function to extract text from PDF using pdfplumber (for text-based PDFs)
def extract_text_with_pdfplumber(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            text = " ".join(page.extract_text() for page in pdf.pages if page.extract_text())
            return text
    except Exception as e:
        print(f"pdfplumber failed: {e}")
        return None

# Function to extract text from PDF using PyMuPDF and OCR (for image-based PDFs)
def extract_text_with_ocr(file_path):
    try:
        doc = fitz.open(file_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"OCR failed: {e}")
        return None

# Function to extract text from PDF or text file
def get_resume_text(file_path):
    if file_path.endswith(".pdf"):
        # Try pdfplumber first
        text = extract_text_with_pdfplumber(file_path)
        if text:
            return text
        # Fallback to OCR if pdfplumber fails
        text = extract_text_with_ocr(file_path)
        if text:
            return text
        raise Exception("Failed to extract text from PDF.")
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# Function to check if a skill is present in the resume
def has_skill(resume_text, skill):
    return skill.lower() in resume_text.lower()

# Function to parse user-input skills
def parse_criteria(user_input):
    required = []
    optional = []
    weights = {}

    parts = user_input.split(";")
    for part in parts:
        if "Required" in part:
            skills = re.findall(r"(\w+)", part.replace("Required:", ""), re.IGNORECASE)
            required = [skill.strip() for skill in skills if skill.strip()]
            for skill in required:
                weights[skill] = 0.4  # Default weight for required
        if "Optional" in part:
            skills = re.findall(r"(\w+)", part.replace("Optional:", ""), re.IGNORECASE)
            optional = [skill.strip() for skill in skills if skill.strip()]
            for skill in optional:
                weights[skill] = 0.2  # Default weight for optional
    return {"required": required, "optional": optional, "weights": weights}

# Function to score a resume based on skill presence
def score_resume(resume_text, criteria):
    score = 0
    max_score = sum(criteria["weights"].values())

    for skill in criteria["required"]:
        if has_skill(resume_text, skill):
            score += criteria["weights"][skill]

    for skill in criteria["optional"]:
        if has_skill(resume_text, skill):
            score += criteria["weights"][skill]

    return (score / max_score) * 100 if max_score > 0 else 0

# Function to generate detailed report
def detailed_report(resume_text, criteria):
    report = []
    for skill in criteria["required"]:
        report.append(f"{skill}: {'Present' if has_skill(resume_text, skill) else 'Missing'}")
    for skill in criteria["optional"]:
        report.append(f"{skill}: {'Present' if has_skill(resume_text, skill) else 'Missing'}")
    return ", ".join(report)

# Route to serve the frontend
@app.route("/")
def index():
    return render_template("index.html")

# API endpoint to screen resumes
@app.route("/screen-resumes", methods=["POST"])
def screen_resumes():
    skills_input = request.form.get("skills")
    files = request.files.getlist("resumes")

    if not skills_input or not files:
        return jsonify({"error": "Please provide skills and upload at least one resume."}), 400

    criteria = parse_criteria(skills_input)
    if not criteria:
        return jsonify({"error": "Invalid skills input."}), 400

    results = []
    for file in files:
        try:
            file_path = os.path.join("uploads", file.filename)
            file.save(file_path)
            resume_text = get_resume_text(file_path)
            score = score_resume(resume_text, criteria)
            details = detailed_report(resume_text, criteria)
            results.append({
                "resume": file.filename,
                "score": round(score, 2),
                "details": details,
            })
        except Exception as e:
            results.append({
                "resume": file.filename,
                "score": 0,
                "details": f"Error processing: {str(e)}",
            })

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)