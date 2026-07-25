import os
import re
import tempfile
import traceback
import uuid

from flask import Flask, render_template, request, send_file, flash, redirect, url_for

from main import generate_report
from LLM import SUPPORTED_MIME_TYPES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "generated_reports")
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-not-for-production")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB upload cap

ALLOWED_EXTENSIONS = set(SUPPORTED_MIME_TYPES.keys())


def _safe_filename_stem(name: str) -> str:
    """Turn a user-supplied company name into a filesystem-safe filename stem."""
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", name.strip()).strip("_")
    return stem or "report"


@app.route("/", methods=["GET"])
def index():
    return render_template("upload.html")


@app.route("/generate", methods=["POST"])
def generate():
    company_name = request.form.get("company_name", "").strip()
    uploaded_file = request.files.get("context_file")

    if not company_name:
        flash("Company name is required.")
        return redirect(url_for("index"))

    if not uploaded_file or uploaded_file.filename == "":
        flash("Please choose a context document to upload.")
        return redirect(url_for("index"))

    ext = os.path.splitext(uploaded_file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        flash(f"Unsupported file type '{ext}'. Please upload a PDF, TXT, or CSV file.")
        return redirect(url_for("index"))

    # Unique per-request working files so concurrent requests never collide.
    request_id = uuid.uuid4().hex[:8]
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = os.path.join(tmp_dir, f"upload_{request_id}{ext}")
        uploaded_file.save(input_path)

        output_stem = f"{_safe_filename_stem(company_name)}_{request_id}"
        output_pdf = os.path.join(OUTPUT_DIR, f"{output_stem}.pdf")
        output_html = os.path.join(tmp_dir, f"{output_stem}.html")

        try:
            generate_report(input_path, output_pdf, output_html, company_name_override=company_name)
        except Exception as exc:
            traceback.print_exc()
            flash(f"Report generation failed: {exc}")
            return redirect(url_for("index"))

    download_name = f"{_safe_filename_stem(company_name)}_report.pdf"
    return send_file(output_pdf, as_attachment=True, download_name=download_name, mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
