import os, mimetypes
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from compressor.pdf_compressor import compress_pdf
from compressor.image_compressor import compress_image
from compressor.doc_compressor import compress_doc
from werkzeug.utils import secure_filename

# --- Flask Config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "compressed")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)

# --- Auto Detect + Compress ---
def auto_compress(file_path):
    file_type, _ = mimetypes.guess_type(file_path)
    filename, ext = os.path.splitext(file_path)
    output_file = os.path.join(
        OUTPUT_FOLDER,
        os.path.basename(filename) + "_compressed" + (ext if ext else ".zip")
    )

    if file_type:
        if "pdf" in file_type:
            compress_pdf(file_path, output_file)
        elif "image" in file_type:
            compress_image(file_path, output_file)
        elif "msword" in file_type or "officedocument" in file_type or ext.lower() in [".docx", ".txt"]:
            compress_doc(file_path, output_file + ".zip")
        

    return output_file

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            return "⚠️ No file uploaded!"

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        name, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext in [".jpg", ".jpeg", ".png"]:
            output_path = os.path.join(OUTPUT_FOLDER, name + "_compressed.jpg")
            success = compress_image(input_path, output_path)
        elif ext == ".pdf":
            output_path = os.path.join(OUTPUT_FOLDER, name + "_compressed.pdf")
            success = compress_pdf(input_path, output_path)
        elif ext == ".docx":
            output_path = os.path.join(OUTPUT_FOLDER, name + "_compressed.docx")
            success = compress_doc(input_path, output_path)

        else:
            return "⚠️ Unsupported file type!"

        if success and os.path.exists(output_path):
            return send_file(output_path, as_attachment=True)
        else:
            return "❌ Compression failed! File not created."

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
