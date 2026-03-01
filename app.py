from flask import Flask, request, jsonify
import pdfplumber
import tempfile
import os

app = Flask(__name__)

# ---------- HEALTH CHECK (IMPORTANTE PARA RENDER) ----------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# ---------- EXTRAER TEXTO + TABLAS ----------
@app.route("/extract", methods=["POST"])
def extract_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    pdf_file = request.files["file"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_file.save(tmp.name)
        tmp_path = tmp.name

    text_pages = []
    tables = []

    try:
        with pdfplumber.open(tmp_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text_pages.append({
                    "page": page_num,
                    "text": page.extract_text()
                })

                page_tables = page.extract_tables()
                for table in page_tables:
                    tables.append({
                        "page": page_num,
                        "rows": table
                    })

    finally:
        os.remove(tmp_path)

    return jsonify({
        "pages": text_pages,
        "tables": tables
    })
    

# ---------- ENTRYPOINT ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
