from flask import Flask, request, send_file, render_template, url_for, send_from_directory, jsonify
import fitz  # PyMuPDF
import os
import re
from PIL import Image
import io

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def is_circle(bbox):
    """Check if the bounding box is circular and larger than 30px."""
    width = bbox.x1 - bbox.x0
    height = bbox.y1 - bbox.y0
    return width > 30 and height > 30 and abs(width - height) < 5


def save_image(image_data, image_number):
    """Save image bytes to the uploads directory."""
    image = Image.open(io.BytesIO(image_data))
    image_path = os.path.join(UPLOAD_FOLDER, f'image_{image_number}.png')
    image.save(image_path)
    return image_path


def redact_names_and_individuals(page, name_pattern, word_to_remove):
    """Redact names and the word 'Individual' from the page."""
    text = page.get_text("text")
    for match in name_pattern.finditer(text):
        new_name = f"{match.group(2)} {match.group(1)}"  # Rearrange name
        for inst in page.search_for(match.group()):
            page.add_redact_annot(inst, fill=(1, 1, 1))
            page.apply_redactions()
            page.insert_text(inst[:2], new_name, fontsize=12, fontname="helv")

    for inst in page.search_for(word_to_remove):
        page.add_redact_annot(inst, fill=(1, 1, 1))
        page.apply_redactions()
        page.insert_text(inst[:2], " ", fontsize=12, fontname="helv")


def extract_images_from_page(doc, page, image_number):
    """Extract circular images from a page."""
    images_on_pages = []
    for img in page.get_images(full=True):
        xref = img[0]
        img_bbox = fitz.Rect(page.get_image_bbox(img))
        if is_circle(img_bbox):
            image_number += 1
            base_image = doc.extract_image(xref)
            image_data = base_image["image"]
            image_path = save_image(image_data, image_number)
            images_on_pages.append({
                'x0': img_bbox.x0, 'y0': img_bbox.y0,
                'x1': img_bbox.x1, 'y1': img_bbox.y1,
                'image_path': image_path
            })
    return images_on_pages, image_number


def process_pdf(input_pdf_path, output_pdf_path):
    """Replace names and extract circular images from PDF."""
    doc = fitz.open(input_pdf_path)
    name_pattern = re.compile(r'(\b[A-Z][a-zA-Z]+), ([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)*)')
    word_to_remove = "Individual"
    images_on_pages = []
    image_number = 0

    for page_num, page in enumerate(doc):
        redact_names_and_individuals(page, name_pattern, word_to_remove)
        page_images, image_number = extract_images_from_page(doc, page, image_number)
        images_on_pages.extend([{'page': page_num, **img} for img in page_images])

    doc.save(output_pdf_path)
    doc.close()
    return images_on_pages


@app.route('/')
def index():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file or not file.filename:
        return "No selected file", 400

    input_pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_pdf_path = os.path.join(UPLOAD_FOLDER, f'modified_{file.filename}')
    file.save(input_pdf_path)

    images_on_pages = process_pdf(input_pdf_path, output_pdf_path)
    return render_template('display.html', 
                           pdf_url=url_for('serve_pdf', filename=f'modified_{file.filename}'),
                           images=images_on_pages, filename=f'modified_{file.filename}')


@app.route('/uploads/<filename>')
def serve_pdf(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)


@app.route('/image/<image_name>')
def serve_image(image_name):
    return send_from_directory(UPLOAD_FOLDER, image_name)


if __name__ == '__main__':
    app.run(debug=True)
