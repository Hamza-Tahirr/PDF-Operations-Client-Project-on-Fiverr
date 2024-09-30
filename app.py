# /app.py
from flask import Flask, request, send_file, render_template, url_for, send_from_directory
import fitz  # PyMuPDF
import os
import re

app = Flask(__name__)

def is_circle(bbox):
    """Check if the bounding box is larger than 20px and approximately circular."""
    width = bbox.x1 - bbox.x0
    height = bbox.y1 - bbox.y0
    # Ensure both width and height are greater than 20px and check if it's approximately circular
    return width > 20 and height > 20 and abs(width - height) < 5

def replace_names_in_pdf(input_pdf_path, output_pdf_path):
    doc = fitz.open(input_pdf_path)
    
    # Regex pattern to match "Last, First Middle" (handles multiple first/middle names)
    name_pattern = re.compile(r'(\b[A-Z][a-zA-Z]+), ([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)*)')
    word_to_remove = "Individual"  # Word to be removed
    images_on_pages = []

    for page_num, page in enumerate(doc):
        # Extract full text from the page
        text = page.get_text("text")

        # Find all matches for "Last, First Middle" pattern
        name_matches = name_pattern.finditer(text)

        for match in name_matches:
            last_name = match.group(1)
            first_middle_names = match.group(2)
            new_name = f"{first_middle_names} {last_name}"

            areas = page.search_for(match.group())
            for inst in areas:
                page.add_redact_annot(inst, fill=(1, 1, 1))  # Redact old name
                page.apply_redactions()

                page.insert_text(inst[:2], new_name, fontsize=12, fontname="helv")

        individual_areas = page.search_for(word_to_remove)
        for inst in individual_areas:
            page.add_redact_annot(inst, fill=(1, 1, 1))  # Redact the word "Individual"
            page.apply_redactions()

            page.insert_text(inst[:2], " ", fontsize=12, fontname="helv")

        # Search for images and store circular bounding boxes larger than 20px
        image_list = page.get_images(full=True)
        for img in image_list:
            img_bbox = fitz.Rect(page.get_image_bbox(img))
            if is_circle(img_bbox):  # Only consider images larger than 20px
                images_on_pages.append({
                    'page': page_num,
                    'x0': img_bbox.x0,
                    'y0': img_bbox.y0,
                    'x1': img_bbox.x1,
                    'y1': img_bbox.y1
                })

    doc.save(output_pdf_path)
    doc.close()

    return images_on_pages

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

    # Replace names in the PDF and remove the word "Individual"
    images_on_pages = replace_names_in_pdf(input_pdf_path, output_pdf_path)

    # Display the modified PDF and pass filename to the template
    return render_template(
        'display.html', 
        pdf_url=url_for('serve_pdf', filename=f'modified_{file.filename}'), 
        images=images_on_pages,
        filename=f'modified_{file.filename}'  
    )

@app.route('/uploads/<filename>')
def serve_pdf(filename):
    return send_from_directory('uploads', filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join('uploads', filename), as_attachment=True)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
