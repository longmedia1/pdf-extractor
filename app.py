from flask import Flask, request, jsonify
import pdfplumber
import tempfile
import os

app = Flask(__name__)

@app.get("/health")
def health():
    return "ok", 200

@app.post("/extract-pdf")
def extract_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file field. Use form-data key: file"}), 400

    f = request.files["file"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        f.save(tmp.name)
        path = tmp.name

    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)

    os.remove(path)
    return jsonify({"text": "\n".join(text_parts)})
