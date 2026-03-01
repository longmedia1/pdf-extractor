from flask import Flask, request, jsonify
import pdfplumber
import tempfile
import os

app = Flask(__name__)

# Endpoint raíz (para Render / wake-up)
@app.get("/")
def root():
    return "ok", 200

# Healthcheck (útil para n8n)
@app.get("/health")
def health():
    return "ok", 200

# Endpoint principal: extraer texto del PDF
@app.post("/extract-pdf")
def extract_pdf():
    if "file" not in request.files:
        return jsonify({
            "error": "No file field. Use form-data with key 'file'"
        }), 400

    file = request.files["file"]

    # Guardar PDF temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        path = tmp.name

    text_parts = []

    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
    finally:
        os.remove(path)

    full_text = "\n".join(text_parts)

    return jsonify({
        "text": full_text
    })
