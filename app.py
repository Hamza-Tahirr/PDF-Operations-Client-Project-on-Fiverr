import os
from flask import Flask, render_template, request, redirect, send_file
import fitz  # PyMuPDF
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_and_print_names(doc):
    all_names = []
    
    # Iterate over all pages in the document
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_instances = page.get_text("text").splitlines()

        for line in text_instances:
            if ',' in line:
                # This is a comma-separated name, split and print
                last_name, first_name = line.split(',', 1)
                full_name = f"{first_name.strip()} {last_name.strip()}"
                all_names.append(full_name)
    
    # Print all extracted names to the terminal
    print("\nExtracted Names:")
    for name in all_names:
        print(name)
    print("\n")  # Extra line for readability

    return all_names

def remove_comma_separated_text(doc):
    # Iterate over all pages in the document
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_instances = page.get_text("text").splitlines()

        for line in text_instances:
            if ',' in line:
                # This is a comma-separated name, search and redact
                rects = page.search_for(line)
                for rect in rects:
                    page.add_redact_annot(rect, fill=[255, 255, 255])  # Redact with white color

        page.apply_redactions()

def remove_word_individual(doc):
    # Iterate over all pages in the document
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Search for the word "Individual" on each page
        rects = page.search_for("Individual")
        
        # Redact all instances of the word "Individual"
        for rect in rects:
            page.add_redact_annot(rect, fill=[255, 255, 255])  # Redact with white color

        page.apply_redactions()

def add_names_to_images(names):
    images = []
    
    # Assuming you have images named 'image1.png', 'image2.png', etc.
    for i, name in enumerate(names):
        image_path = f'images/image{i + 1}.png'  # Adjust path as needed
        if os.path.exists(image_path):
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)

            # Define font size and type (ensure this font exists on your system)
            font_size = 20
            font = ImageFont.load_default()

            # Position to draw text (adjust as needed)
            text_position = (10, img.height - 30)  # Bottom-left corner
            
            draw.text(text_position, name, fill="black", font=font)
            output_image_path = f'output/image_with_name_{i + 1}.png'
            img.save(output_image_path)
            images.append(output_image_path)

    return images

def remove_comma_text_from_pdf(file):
    # Open the uploaded PDF
    doc = fitz.open(stream=file.read(), filetype="pdf")
    
    # Step 1: Extract names to terminal and return list of names
    extracted_names = extract_and_print_names(doc)
    
    # Step 2: Remove all comma-separated names from the PDF
    remove_comma_separated_text(doc)

    # Step 3: Remove the word "Individual" from the PDF
    remove_word_individual(doc)

    # Save the modified PDF
    output_pdf = BytesIO()
    doc.save(output_pdf)
    output_pdf.seek(0)

    # Step 4: Add extracted names to images
    add_names_to_images(extracted_names)

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

    # Extract names, remove comma-separated names, and remove "Individual"
    modified_pdf = remove_comma_text_from_pdf(file)

    return send_file(modified_pdf, download_name='modified.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)