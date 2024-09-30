# /app.py
from flask import Flask, request, send_file, render_template, url_for, send_from_directory
import fitz  # PyMuPDF
import os
import re

app = Flask(__name__)

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
            last_name = match.group(1)  # Last name
            first_middle_names = match.group(2)  # First and any middle names
            new_name = f"{first_middle_names} {last_name}"

            # Get the position of the text in the PDF
            areas = page.search_for(match.group())
            for inst in areas:
                # Redact the old name
                page.add_redact_annot(inst, fill=(1, 1, 1))  # White out old name
                page.apply_redactions()

                # Insert the new name in the same position (adjust position and size if needed)
                page.insert_text(inst[:2], new_name, fontsize=12, fontname="helv")

        # Search for the word "Individual"
        individual_areas = page.search_for(word_to_remove)
        for inst in individual_areas:
            # Redact the word "Individual" and replace with space
            page.add_redact_annot(inst, fill=(1, 1, 1))  # White out the word
            page.apply_redactions()

            # Optionally, you can leave this space empty, or just replace it with an actual space.
            page.insert_text(inst[:2], " ", fontsize=12, fontname="helv")

        # Search for images and store their bounding boxes
        image_list = page.get_images(full=True)
        for img in image_list:
            img_bbox = fitz.Rect(page.get_image_bbox(img))
            images_on_pages.append({
                'page': page_num,
                'x0': img_bbox.x0,  # Extract the x0 coordinate
                'y0': img_bbox.y0   # Extract the y0 coordinate
            })

    # Save the modified PDF
    doc.save(output_pdf_path)
    doc.close()

    return images_on_pages  # Return the list of images to display checkboxes

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
        filename=f'modified_{file.filename}'  # Pass the modified filename to the template
    )

@app.route('/uploads/<filename>')
def serve_pdf(filename):
    # Serve the modified PDF from the uploads directory
    return send_from_directory('uploads', filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join('uploads', filename), as_attachment=True)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
