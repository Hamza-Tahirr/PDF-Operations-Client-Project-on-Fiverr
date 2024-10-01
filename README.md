# PDF Redaction and Image Extraction Tool

This is a Flask-based web application that allows users to upload PDF files, automatically redact names and the word "Individual" from the documents, and extract circular images larger than 30px. The modified PDF and extracted images are displayed to the user for download or printing.

## Features

- **PDF Upload**: Users can upload a PDF document via the web interface.
- **Text Redaction**: The application automatically redacts names (formatted as `LastName, FirstName`) and the word "Individual" from the PDF.
- **Image Extraction**: Circular images larger than 30px are extracted from the PDF and saved to the server.
- **PDF Preview**: The redacted PDF is displayed in-browser with options to download the modified file.
- **Image Gallery**: Extracted images are shown in a gallery with information about their coordinates within the PDF.
- **Print Images**: Users can view and print extracted images directly from the browser.

## Technologies Used

- **Python** (Flask framework)
- **PyMuPDF** (for PDF manipulation and image extraction)
- **Pillow** (for image processing)
- **HTML/CSS** (with Bootstrap for responsive design)
- **JavaScript** (for modal and image gallery functionality)

## Installation

1. Clone the repository:
    ```bash
    git clone [https://github.com/your-username/pdf-redaction-image-extraction.git](https://github.com/Hamza-Tahirr/PDF-Operations-Client-Project-on-Fiverr.git)
    cd pdf-redaction-image-extraction
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

    > **Note:** The main dependencies are `Flask`, `PyMuPDF`, and `Pillow`. Make sure to install these in your environment.

3. Run the Flask application:
    ```bash
    python app.py
    ```

4. Access the application in your web browser at `http://127.0.0.1:5000/`.

## Usage

1. Open the application in your browser.
2. Upload a PDF file using the **Upload PDF** page.
3. The application will process the PDF, redact specified names and words, and extract circular images.
4. The redacted PDF will be displayed on the **PDF Display** page, along with a gallery of extracted images.
5. You can:
   - **Download** the redacted PDF file.
   - **View** and **print** extracted images.

## File Structure

```plaintext
├── app.py                # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   ├── upload.html        # HTML template for PDF upload page
│   ├── display.html       # HTML template for PDF and image display page
├── static/
│   ├── css/               # Optional CSS files (for additional styling)
│   └── js/                # Optional JavaScript files
└── uploads/               # Directory to store uploaded and processed files
