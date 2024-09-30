import os
from flask import Flask, render_template, request, redirect, send_file
import fitz  # PyMuPDF
from io import BytesIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def format_names(text):
    # Split text by lines and format each name
    formatted_names = []
    for line in text.splitlines():
        if ',' in line:
            last_name, first_name = line.split(',', 1)
            formatted_names.append(f"{first_name.strip()} {last_name.strip()}")
    return formatted_names

def replace_names_in_pdf(doc, formatted_names):
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_instances = page.get_text("text").splitlines()
        
        # Replace old names with new formatted names
        for i, old_name in enumerate(text_instances):
            if ',' in old_name:
                formatted_name = format_names(old_name)
                if formatted_name:
                    rects = page.search_for(old_name)
                    for name in formatted_name:
                        for rect in rects:
                            page.insert_text(rect[:2], name, fontsize=12)  # Adjust fontsize as needed
                            # Now, find and remove the next line if it still contains a comma-separated name
                            if i + 1 < len(text_instances) and ',' in text_instances[i + 1]:
                                remove_comma_separated_line(page, text_instances[i + 1])

        page.apply_redactions()

def remove_comma_separated_line(page, line):
    # Find and remove lines containing comma-separated names (after replacement)
    rects = page.search_for(line)
    for rect in rects:
        page.add_redact_annot(rect, fill=[255, 255, 255])

def remove_word_from_pdf(file, word):
    # Open the uploaded PDF
    doc = fitz.open(stream=file.read(), filetype="pdf")
    
    # Step 1: Remove the word "Individual"
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_instances = page.search_for(word)
        
        for inst in text_instances:
            page.add_redact_annot(inst, fill=[255, 255, 255])
    
    # Extract all text from the PDF
    all_text = ""
    for page_num in range(len(doc)):
        all_text += doc[page_num].get_text()

    formatted_names = format_names(all_text)

    # Step 2: Replace names in PDF with formatted names
    replace_names_in_pdf(doc, formatted_names)

    output_pdf = BytesIO()
    doc.save(output_pdf)
    output_pdf.seek(0)
    return output_pdf



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']

    if file.filename == '' or not allowed_file(file.filename):
        return redirect(request.url)

    # Remove both "Individual" and comma-separated names
    modified_pdf = remove_word_from_pdf(file, 'Individual')

    return send_file(modified_pdf, download_name='modified.pdf', as_attachment=True)

if __name__ == '__main__': 
    app.run(debug=True)
