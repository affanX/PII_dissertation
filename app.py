from flask import Flask, request, send_file, render_template
import pdfplumber
from fpdf import FPDF
import spacy
import os
import re

app = Flask(__name__)

# Load the trained spaCy NER model
MODEL_PATH = "ner_model"
if os.path.exists(MODEL_PATH):
    nlp = spacy.load(MODEL_PATH)
else:
    raise FileNotFoundError("Trained NER model not found. Train the model first!")

# Function to redact text
def redact_entities(text, nlp_model):
    doc = nlp_model(text)
    redacted_text = text
    for ent in doc.ents:
        redacted_text = re.sub(re.escape(ent.text), "[REDACTED]", redacted_text)
    return redacted_text

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file and file.filename.endswith('.pdf'):
        try:
            input_pdf_path = os.path.join("uploads", "uploaded.pdf")
            redacted_pdf_path = os.path.join("outputs", "redacted.pdf")
            
            # Create directories if they don't exist
            os.makedirs("uploads", exist_ok=True)
            os.makedirs("outputs", exist_ok=True)

            # Save uploaded PDF
            file.save(input_pdf_path)

            # Process PDF
            with pdfplumber.open(input_pdf_path) as pdf:
                pdf_writer = FPDF()
                for page in pdf.pages:
                    text = page.extract_text()
                    redacted_text = redact_entities(text, nlp) if text else ""
                    
                    # Add redacted text to PDF
                    pdf_writer.add_page()
                    pdf_writer.set_font("Arial", size=12)
                    pdf_writer.multi_cell(0, 10, redacted_text)
            
            # Output the redacted PDF
            pdf_writer.output(redacted_pdf_path)
            
            return send_file(redacted_pdf_path, as_attachment=True)

        except Exception as e:
            return f"An error occurred: {str(e)}", 500

    return "Invalid file format. Please upload a PDF.", 400

if __name__ == '__main__':
    app.run(debug=True)
