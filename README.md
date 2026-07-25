# Equity Research Report Generator

Upload a company's financial context document (PDF, TXT, or CSV) and get back a
downloadable, auto-filled equity research report PDF styled after Geojit's
"Retail Equity Research" template.

## How it works (pipeline)

```
context document (PDF/TXT/CSV)
        |
        v
   LLM.py            Gemini extracts structured data into the ReportData schema
        |
        v
  schema.py           Pydantic models = the contract between the LLM and the template
        |
        v
context_builder.py    Reshapes ReportData into the flat dict the Jinja template expects
        |
        v
chart_generator.py     Renders matplotlib charts -> base64 PNG data-URIs
        |
        v
report_template.html  Jinja2 template (styled for WeasyPrint / print)
        |
        v
     WeasyPrint         Renders the filled HTML to PDF
        |
        v
  output PDF
```

`main.py` wires all of the above into one `generate_report()` call, used by
both the CLI and the web UI (`app.py`).

## Where the template fields are defined

- **`schema.py`** — the source of truth for every field the LLM is asked to
  extract (`ReportData` and its nested models: `HeaderInfo`, `CompanyData`,
  `ShareholdingRow`, `PricePerformanceRow`, `KeyMetricsRow`,
  `QuarterlyFinancialRow`, `ChartData`, `FinancialStatementRow`,
  `RecommendationRow`). To extract a new field, add it here first.
- **`LLM.py`** — the extraction prompt (`PROMPT`) passed to Gemini alongside
  the schema. Field-specific extraction guidance (e.g. what counts as the
  report's `headline` vs. its `business_summary`) lives here as prompt notes.
- **`context_builder.py`** — maps the nested `ReportData` object into the flat
  `{key: value}` dict the Jinja template consumes (e.g. transposing
  `key_metrics` from one-row-per-year into one-row-per-metric, or converting a
  `ShareholdingRow` list into `{shareholding_rows, shareholding_quarters,
  shareholding_total}`). Also holds static broker boilerplate
  (`STATIC_BROKER_INFO`) that isn't extracted per-company, and safe defaults
  for fields the schema doesn't (yet) capture (`NOT_YET_EXTRACTED_DEFAULTS`).
- **`report_template.html`** — the actual layout: every `{{ field }}` /
  `{% for row in rows %}` placeholder here corresponds to a key produced by
  `context_builder.build_context()`.
- **`chart_generator.py`** — turns `ReportData.charts`, `.price_performance`,
  and `.recommendation_history` into rendered chart images, keyed by the same
  titles the template's `charts_row1`/`charts_row2`/`price_chart_img_url`/
  `recommendation_chart_img_url` placeholders look up.

Missing fields are never fabricated: the LLM prompt instructs Gemini to leave
absent fields `null`, and `context_builder.py` renders those as `"N/A"` (or a
computed fallback, e.g. summing shareholding rows if no explicit "Total" row
was extracted) rather than guessing.

## Tech used

| Piece | Tech |
|---|---|
| LLM extraction | Google Gemini (`google-genai`), structured output via a Pydantic response schema |
| Data modeling | Pydantic |
| Templating | Jinja2 |
| PDF rendering | WeasyPrint (HTML/CSS -> PDF) |
| Charts | Matplotlib, embedded as base64 PNG data-URIs (no static file serving needed) |
| Web UI | Flask |

## Running it

### Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in GEMINI_API_KEY
```

WeasyPrint depends on native GTK libraries (Pango/Cairo/GObject) that aren't
installable via pip alone:
- **Windows**: install the [GTK3 runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases), restart your terminal.
- **macOS**: `brew install pango cairo gdk-pixbuf libffi`
- **Linux**: `apt install libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf2.0-0`

See the [WeasyPrint install docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation) if you hit import errors.

### Option A: Web UI

```bash
python app.py
```

Visit `http://127.0.0.1:5000`, enter a company name, upload a PDF/TXT/CSV
context document, and click **Generate & Download PDF**.

### Option B: CLI

```bash
python main.py path/to/context_document.pdf --out my_report.pdf --company-name "Example Ltd."
```

Run `python main.py --help` for all flags. `input_path` is required (no bundled
default file) -- point it at any PDF/TXT/CSV context document.

## Project structure

```
schema.py              Pydantic models -- the extraction target
LLM.py                 Gemini extraction call + prompt
context_builder.py     ReportData -> Jinja context dict
chart_generator.py     matplotlib chart rendering
report_template.html   the PDF layout (Jinja2 + CSS, WeasyPrint-targeted)
main.py                generate_report() -- the pipeline entry point + CLI
app.py                 Flask web UI (upload -> generate -> download)
templates/upload.html  the UI's upload form
test_inputs/           sample TXT/CSV context documents used to validate multi-format support
examples/               example generated PDFs (see note below)
```

## Example generated PDFs

`examples/` contains PDFs generated by this pipeline, run against the
assessment's actual provided test documents:

- `eternal_ltd_report.pdf` — from the provided `Eternal-Geojit.pdf` sample
  (Geojit-style sell-side analyst research note; closest match to the target
  template's genre — fully populated).
- `pocl_report.pdf` — from POCL's Q2 FY26 investor presentation (a
  company-issued investor deck, not a sell-side analyst note).
- `jsw_energy_report.pdf` — from JSW Energy's Q2 FY26 results presentation
  (same genre as POCL: company-issued, not analyst-issued).

### Note on document genre

The assessment's provided test documents include both sell-side equity
research notes (Eternal) and company-issued investor/results presentations
(POCL, JSW Energy). The schema and template were reverse-engineered from the
Geojit sample, which is the former genre. For investor-deck-style documents,
sections with no equivalent in the source (analyst rating, target price,
recommendation history, forward broker estimates) correctly degrade to "N/A"
per the "handles missing fields gracefully" requirement, rather than being
fabricated. Narrative sections, business summary, key highlights, and
multi-period financial tables generally populate well for this genre too.

`nova_retail_report.pdf` and `aster_pharma_report.pdf` (from synthetic
TXT/CSV files in `test_inputs/`, written to validate multi-format extraction
since PDF is the only format among the assessment's actual provided docs)
remain in `examples/` as the TXT/CSV format-coverage proof.

## Known limitations

- **Page-fit edge case**: on dense inputs, the Company Data / Shareholding /
  Price Performance / Summary Financials column on page 1 can occasionally run
  ~1 line over a single page, pushing one table onto an otherwise-empty page 2.
  Tables never get sliced mid-row (each table either fits whole or moves whole
  to the next page), so nothing renders as a broken/garbled table -- it's a
  cosmetic layout issue, not a data issue.
- **No historical price chart**: the original Geojit sample's page-1 chart is
  a ~1-year daily price line; the extraction schema has no daily price time
  series field (that would need a market-data feed, not a context document),
  so that box instead shows a 3M/6M/1Y return comparison chart built from data
  the schema does capture.
- **Logo/signature**: `logo_url` and `signature_img_url` are 1x1 placeholder
  images (no brand asset was provided). Swap real values into
  `context_builder.STATIC_BROKER_INFO` to use an actual logo/signature.
- Chart bar+line dual-axis combos from the original sample were deliberately
  rebuilt as single-axis bars with direct value/growth labels instead --
  dual-axis (two y-scales on one chart) is a well-known chart-reading pitfall.
- **Chart extraction did not populate for the POCL example** despite the
  source deck containing bar charts that should fit `ChartData`'s shape (a
  title, x-axis categories, and a bar series). Root cause not yet isolated --
  most likely Gemini simply didn't extract `ReportData.charts` for that
  particular document (extraction is not perfectly deterministic run-to-run;
  the same non-population happened once on the Eternal PDF before a re-run
  succeeded), but this hasn't been confirmed by re-running against the actual
  POCL file. Worth a follow-up before treating POCL as the headline example.
