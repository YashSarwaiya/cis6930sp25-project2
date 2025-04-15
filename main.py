import os
import sys
import glob
import argparse
import fitz  # PyMuPDF
import spacy
import requests

# Ensure Python 3.10 or later is used.
if sys.version_info < (3, 10):
    sys.exit("Error: Python 3.10 or higher is required for this project.")

def process_names(page, file_name, sensitive_names, stats_entries, page_no):
    """Search for each sensitive name on the page, add a redaction annotation, and log stats."""
    for name in sensitive_names:
        # Find all occurrences on the page (case-sensitive search)
        rects = page.search_for(name)
        for rect in rects:
            page.add_redact_annot(rect, fill=(0, 0, 0))
            # Log redaction: location as page number and top-left (x0,y0) of the rectangle (rounded)
            loc = f"{page_no}:{int(rect.x0)}x{int(rect.y0)}"
            stats_entries.append(f"{file_name}\t{loc}\t{name}\t{len(name)}\tName")
    return

def process_entities(page, file_name, nlp, redact_all, stats_entries, page_no):
    """Run NER on the page text; if the --entities flag is provided redact all entities,
       otherwise only PERSON entities."""
    text = page.get_text()
    doc = nlp(text)
    for ent in doc.ents:
        # Redact only PERSON entities by default; if --entities is set, redact all.
        if not redact_all and ent.label_ != "PERSON":
            continue
        token = ent.text.strip()
        if not token:
            continue
        rects = page.search_for(token)
        for rect in rects:
            page.add_redact_annot(rect, fill=(0, 0, 0))
            loc = f"{page_no}:{int(rect.x0)}x{int(rect.y0)}"
            stats_entries.append(f"{file_name}\t{loc}\t{token}\t{len(token)}\tEntity")
    return

def process_coref(page, file_name, stats_entries, page_no):
    text = page.get_text()
    url = "http://gpu002.cm.cluster:65535/resolve_coref"
    headers = {"Content-Type": "application/json"}
    payload = {"text": text}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            mapping = data.get("coreference_mapping", [])
            for cluster in mapping:
                for token in cluster.values():
                    token = token.strip()
                    if not token:
                        continue
                    rects = page.search_for(token)
                    for rect in rects:
                        page.add_redact_annot(rect, fill=(0, 0, 0))
                        loc = f"{page_no}:{int(rect.x0)}x{int(rect.y0)}"
                        stats_entries.append(f"{file_name}\t{loc}\t{token}\t{len(token)}\tCoref")
        else:
            print(f"Coref API returned status {response.status_code} for file {file_name} on page {page_no}", file=sys.stderr)
    except Exception as e:
        print(f"Error during coref resolution for file {file_name} on page {page_no}: {e}", file=sys.stderr)
    return

def process_pdf(file_path, output_dir, sensitive_names, nlp, redact_all_entities, do_coref, stats_entries):
    """Open the PDF file, process each page for redaction based on names, entities, and coreference,
       then save the redacted document to the output directory."""
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        print(f"Error opening {file_path}: {e}", file=sys.stderr)
        return

    file_name = os.path.basename(file_path)
    for page_no in range(len(doc)):
        page = doc[page_no]
        # Process redaction for names (if provided)
        if sensitive_names:
            process_names(page, file_name, sensitive_names, stats_entries, page_no)
        # Process redaction for named entities (using spaCy)
        process_entities(page, file_name, nlp, redact_all_entities, stats_entries, page_no)
        # Process redaction for coreferences if the flag is enabled
        if do_coref:
            process_coref(page, file_name, stats_entries, page_no)
        # Apply all redactions on the page
        page.apply_redactions()
    # Save the redacted PDF to the output directory (using the same filename)
    output_file_path = os.path.join(output_dir, file_name)
    doc.save(output_file_path)
    doc.close()
    print(f"Processed and saved redacted file: {output_file_path}")
    return

def write_stats(stats_file, stats_entries):
    """Write the stats log to a file or, if not provided, output to standard error."""
    if stats_file:
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                for entry in stats_entries:
                    f.write(entry + "\n")
        except Exception as e:
            print(f"Error writing stats file: {e}", file=sys.stderr)
    else:
        # If no stats file is provided, output each entry to stderr.
        for entry in stats_entries:
            print(entry, file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Redact sensitive information from PDF documents.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", nargs="+", required=True,
                        help="Input file(s) specified by glob pattern (e.g., --input 'data/*.pdf')")
    parser.add_argument("--output", required=True,
                        help="Output directory for redacted PDF files")
    parser.add_argument("--names", nargs="+",
                        help="One or more case sensitive names/tokens to redact; can be specified multiple times")
    parser.add_argument("--entities", action="store_true",
                        help="Redact all named entities (by default, only PERSON entities are redacted)")
    parser.add_argument("--coref", action="store_true",
                        help="Redact all coreferences using the external coref resolution API")
    parser.add_argument("--stats", help="File path for the output stats file (TSV format)")

    args = parser.parse_args()

    # Create output directory if it does not exist.
    os.makedirs(args.output, exist_ok=True)

    # Expand input file globs into a list of files.
    input_files = []
    for pattern in args.input:
        matched = glob.glob(pattern)
        if not matched:
            print(f"Warning: No files matched pattern: {pattern}", file=sys.stderr)
        input_files.extend(matched)
    if not input_files:
        sys.exit("Error: No input files found; please check your --input parameter.")

    # Load the spaCy model for NER (ensure you have installed en_core_web_sm)
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        sys.exit(f"Error loading spaCy model 'en_core_web_sm': {e}")

    # Stats will be recorded as a list of TSV-formatted strings.
    stats_entries = []
    # Process each input PDF file.
    for file_path in input_files:
        process_pdf(file_path, args.output, args.names, nlp, args.entities, args.coref, stats_entries)

    # Write the stats output.
    write_stats(args.stats, stats_entries)

if __name__ == '__main__':
    main()
