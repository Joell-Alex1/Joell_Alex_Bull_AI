from pathlib import Path
from google import genai
from google.genai import types
import dotenv
from schema import ReportData

dotenv.load_dotenv()
client = genai.Client()

# Explicit mime types for the formats this app accepts. Deliberately not
# relying on Python's mimetypes.guess_type(): on Windows it reads the
# registry, which maps .csv -> "application/vnd.ms-excel" instead of
# "text/csv" -- Gemini's file API expects the latter for a CSV text upload.
SUPPORTED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".csv": "text/csv",
}

PROMPT = """
Extract all financial data, tables, narrative sections, and chart data
from this equity research / financial context document. Return data matching
the given schema exactly. If a field is not present in the document, leave it
as null. Do not fabricate numbers.

The source document may be a formatted PDF report, a plain-text summary, or a
CSV of financial line items -- extract whatever fields are present in
whichever format is given; leave everything else null rather than guessing.

Note: header.headline is the short, bold one-line takeaway printed near the top
of a report (e.g. "Blinkit propels growth; valuation limits upside") -- it is a
distinct editorial tagline, NOT the first sentence of the company/business
description paragraph. Extract it separately from business_summary. If the
source document has no such tagline (e.g. a plain CSV/TXT export), leave it null.
"""


def extract_report_data(file_path: str) -> ReportData:
    """Extract structured report data from a context document.

    Accepts PDF, TXT, or CSV input -- any format Gemini can read as either a
    document or plain text. The mime type is chosen explicitly from the file
    extension rather than OS-guessed (see SUPPORTED_MIME_TYPES).
    """
    ext = Path(file_path).suffix.lower()
    if ext not in SUPPORTED_MIME_TYPES:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_MIME_TYPES)}"
        )

    uploaded_file = client.files.upload(
        file=file_path,
        config=types.UploadFileConfig(mime_type=SUPPORTED_MIME_TYPES[ext]),
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[uploaded_file, PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ReportData,
            ),
        )
    finally:
        client.files.delete(name=uploaded_file.name)

    # response.parsed gives you the validated Pydantic object directly
    return response.parsed