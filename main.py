import argparse
import os

from LLM import extract_report_data
from context_builder import build_context
from chart_generator import build_chart_img_urls
from jinja2 import Environment, FileSystemLoader


def format_number(value):
    """Render numeric values with thousands separators; pass non-numeric values through untouched."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value == int(value):
            return f"{int(value):,}"
        return f"{value:,.1f}"
    return value


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_report(input_path: str, output_pdf: str, output_html: str, company_name_override: str = None) -> None:
    data = extract_report_data(input_path)
    if company_name_override:
        # The user-supplied company name (from the UI form) wins over whatever
        # the LLM extracted -- it's an explicit, trusted input.
        data.header.company_name = company_name_override

    chart_img_urls = build_chart_img_urls(data)
    context = build_context(data, chart_img_urls)

    env = Environment(loader=FileSystemLoader(BASE_DIR))
    env.filters["fmt"] = format_number
    template = env.get_template("report_template.html")
    rendered_html = template.render(**context)

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    from weasyprint import HTML
    HTML(string=rendered_html, base_url=BASE_DIR).write_pdf(output_pdf)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an equity research report PDF from a context document.")
    parser.add_argument("input_path", help="Path to a PDF, TXT, or CSV context document")
    parser.add_argument("--out", default=os.path.join(BASE_DIR, "output_report.pdf"), help="Output PDF path")
    parser.add_argument("--html-out", default=os.path.join(BASE_DIR, "output_preview.html"), help="Output HTML preview path")
    parser.add_argument("--company-name", default=None, help="Override the extracted company name")
    args = parser.parse_args()

    generate_report(args.input_path, args.out, args.html_out, company_name_override=args.company_name)
    print(f"Wrote {args.out}")