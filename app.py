from flask import Flask, request, jsonify
import pdfplumber
import tempfile
import os
import re

app = Flask(__name__)

@app.get("/health")
def health():
    return "ok", 200

def norm_cell(x):
    if x is None:
        return ""
    return re.sub(r"\s+", " ", str(x)).strip()

def guess_header_map(header_row):
    # Mapea nombres de columnas según lo que encuentre
    h = [norm_cell(c).upper() for c in header_row]
    def find(*keys):
        for k in keys:
            for i, col in enumerate(h):
                if k in col:
                    return i
        return None

    return {
        "STS": find("STS"),
        "TIPO": find("TIPO"),
        "DIRECCION": find("DIRECC"),
        "PRECIO": find("PRECIO"),
        "COMISION": find("COMISI"),
        "IBI": find("IBI"),
        "COMUNIDAD": find("COMUN"),
        "FOTOS": find("FOTOS"),
        "OBS": find("OBSERV"),
    }

@app.post("/extract-table")
def extract_table():
    if "file" not in request.files:
        return jsonify({"error": "No file field. Use form-data key: file"}), 400

    f = request.files["file"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        f.save(tmp.name)
        path = tmp.name

    all_tables = []
    rows = []
    full_text_parts = []

    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                # texto fallback
                t = page.extract_text() or ""
                if t:
                    full_text_parts.append(t)

                # intenta extraer tablas
                tables = page.extract_tables() or []
                for table in tables:
                    # limpia
                    clean_table = [[norm_cell(c) for c in r] for r in table if r]
                    # descarta “tablas” vacías
                    if len(clean_table) < 2:
                        continue

                    all_tables.append(clean_table)

                    # intenta convertir a rows con columnas
                    header = clean_table[0]
                    idx = guess_header_map(header)
                    for r in clean_table[1:]:
                        # evita filas muy cortas
                        if len("".join(r)) < 5:
                            continue

                        def get(col):
                            i = idx.get(col)
                            if i is None:
                                return ""
                            return r[i] if i < len(r) else ""

                        sts = get("STS")
                        if sts and re.fullmatch(r"\d{4}", sts):
                            rows.append({
                                "STS": f"STS-{sts}",
                                "TIPO": get("TIPO"),
                                "DIRECCION": get("DIRECCION"),
                                "PRECIO": get("PRECIO"),
                                "COMISION": get("COMISION"),
                                "IBI": get("IBI"),
                                "COMUNIDAD": get("COMUNIDAD"),
                                "FOTOS": get("FOTOS"),
                                "OBS": get("OBS"),
                            })

        return jsonify({
            "rows": rows,
            "tables_count": len(all_tables),
            "rows_count": len(rows),
            "text": "\n".join(full_text_parts)[:200000],  # evita respuestas gigantes
        })

    finally:
        try:
            os.remove(path)
        except:
            pass
