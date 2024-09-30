# /app.py
from flask import Flask, request, send_file, render_template
import fitz  # PyMuPDF
import os
import re

app = Flask(__name__)

def replace_names_in_pdf(input_pdf_path, output_pdf_path):
    doc = fitz.open(input_pdf_path)

    # Regex pattern to match "Last, First" (e.g., Adams, Brie)
    pattern = re.compile(r'(\b[A-Z][a-zA-Z]+), (\b[A-Z][a-zA-Z]+)')

    for page in doc:
        # Extract full text from the page
        text = page.get_text("text")
        
        # Find all matches for "Last, First" pattern
        matches = pattern.finditer(text)
        
        for match in matches:
            last_name, first_name = match.groups()
            new_name = f"{first_name} {last_name}"

            # Get the position of the text in the PDF
            areas = page.search_for(match.group())
            for inst in areas:
                # Redact the old name
                page.add_redact_annot(inst, fill=(1, 1, 1))  # White out old name
                page.apply_redactions()

                # Insert the new name in the same position (adjust position and size if needed)
                page.insert_text(inst[:2], new_name, fontsize=12, fontname="helv")

    # Save the modified PDF
    doc.save(output_pdf_path)
    doc.close()

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    
    if file.filename == '':
        return "No selected file", 400

    input_pdf_path = os.path.join('uploads', file.filename)
    output_pdf_path = os.path.join('uploads', f'modified_{file.filename}')

    # Save the uploaded file
    file.save(input_pdf_path)

    # Replace names in the PDF
    replace_names_in_pdf(input_pdf_path, output_pdf_path)

    # Return the modified PDF to the user
    return send_file(output_pdf_path, as_attachment=True)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
