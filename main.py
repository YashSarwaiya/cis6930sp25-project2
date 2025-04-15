# #!/usr/bin/env python3
# """
# Project 2 – Redacting Statements
# CIS 6930 Spring 2025

# This script redacts sensitive information from PDF documents.
# Redaction tokens include:
#   - Names provided via the --names flag (case sensitive)
#   - Named entities extracted via spaCy (by default only PERSON entities,
#     unless --entities is specified, in which case all entity types are redacted)
#   - Coreference mentions if the --coref flag is supplied

# Redacted areas are logged with stats (file name, location, token, length, type)
# which are output either to a specified stats file or to standard error.
# """

# import argparse
# import glob
# import os
# import sys
# import csv
# import fitz  # PyMuPDF
# import spacy

# def process_pdf(file_path, output_dir, names, redact_all_entities, use_coref, nlp, nlp_coref, stats_list):
#     """
#     Process and redact one PDF file.
    
#     For each page in the PDF:
#       - Extract text.
#       - Run NLP (NER) to obtain named entities (or just PERSON, by default).
#       - If requested, run a coreference model to get coref mentions.
#       - Add tokens from the command-line (names) to the redaction list.
#       - Search for each token in the page and add redaction annotations.
#       - Log every redaction with the file, location, token, length, and type.
#     The modified PDF is saved to output_dir with the same base file name.
#     """
#     try:
#         doc = fitz.open(file_path)
#     except Exception as e:
#         sys.stderr.write(f"Error opening {file_path}: {e}\n")
#         return

#     # Process each page individually.
#     for page_num in range(len(doc)):
#         page = doc[page_num]
#         text = page.get_text("text")
        
#         # Use the base spaCy model for named entity recognition.
#         doc_spacy = nlp(text)
#         redaction_tokens = []  # list of tuples: (token_text, token_type)

#         # From spaCy NER: by default redact only PERSON entities unless --entities is used.
#         for ent in doc_spacy.ents:
#             if redact_all_entities or ent.label_ == "PERSON":
#                 token_type = "Entity" if redact_all_entities else "Name"
#                 redaction_tokens.append((ent.text, token_type))

#         # Add user-supplied names (case sensitive) from the --names flag.
#         for name in names:
#             redaction_tokens.append((name, "Name"))

#         # If coreference redaction is requested, run the coref model.
#         if use_coref and nlp_coref is not None:
#             try:
#                 doc_coref = nlp_coref(text)
#                 # Using spaCy’s experimental coref extension; iterate over clusters.
#                 if hasattr(doc_coref._, "coref_clusters"):
#                     for cluster in doc_coref._.coref_clusters:
#                         for mention in cluster.mentions:
#                             redaction_tokens.append((mention.text, "Coref"))
#             except Exception as e:
#                 sys.stderr.write(f"Coreference processing error on page {page_num+1} of {file_path}: {e}\n")

#         # For each token, search on the page and add redaction annotations.
#         for token_text, token_type in redaction_tokens:
#             token_clean = token_text.strip()
#             if not token_clean:
#                 continue
#             # search_for is case sensitive.
#             rects = page.search_for(token_clean, hit_max=100)
#             for rect in rects:
#                 # Add a redaction annotation with a black fill.
#                 page.add_redact_annot(rect, fill=(0, 0, 0))
#                 # Format location as "Page {page_num}: x0,y0,x1,y1"
#                 location_str = f"Page {page_num+1}: {int(rect.x0)},{int(rect.y0)},{int(rect.x1)},{int(rect.y1)}"
#                 stats_list.append((os.path.basename(file_path), location_str, token_clean, len(token_clean), token_type))
        
#         # Apply redactions on the page.
#         page.apply_redactions()

#     # Save the updated PDF file in the output directory.
#     output_path = os.path.join(output_dir, os.path.basename(file_path))
#     try:
#         doc.save(output_path)
#         print(f"Processed {file_path} --> {output_path}")
#     except Exception as e:
#         sys.stderr.write(f"Error saving redacted PDF {output_path}: {e}\n")
#     finally:
#         doc.close()

# def main():
#     parser = argparse.ArgumentParser(
#         description="Redact sensitive information from PDF documents.",
#         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
#     parser.add_argument("--input", nargs="+", help="Input file glob(s)", required=True)
#     parser.add_argument("--output", help="Output directory for PDF files", required=True)
#     parser.add_argument("--names", nargs="+", help="One or more case sensitive names to redact", default=[])
#     parser.add_argument("--entities", action="store_true",
#                         help="Redact all named entities (if not provided, only PERSON entities are redacted)")
#     parser.add_argument("--coref", action="store_true", help="Redact coreferences in the text")
#     parser.add_argument("--stats", help="Path to the stats file (tab-separated)")
#     args = parser.parse_args()

#     # Create output directory if it does not exist.
#     if not os.path.exists(args.output):
#         os.makedirs(args.output)

#     # Aggregate input file paths using glob (support multiple globs).
#     input_files = []
#     for pattern in args.input:
#         input_files.extend(glob.glob(pattern))
#     if not input_files:
#         sys.stderr.write("No input files found with the given pattern(s).\n")
#         sys.exit(1)

#     # Load the spaCy model for NER.
#     try:
#         nlp = spacy.load("en_core_web_sm")
#     except Exception as e:
#         sys.stderr.write(f"Error loading spaCy model 'en_core_web_sm': {e}\n")
#         sys.exit(1)

#     # Load the coreference resolution model if requested.
#     nlp_coref = None
#     if args.coref:
#         try:
#             nlp_coref = spacy.load("en_coreference_web_trf")
#         except Exception as e:
#             sys.stderr.write(f"Error loading coreference model 'en_coreference_web_trf': {e}\n")
#             sys.exit(1)

#     # List to hold stats records: (File, Location, Token, Length, Type)
#     stats_list = []

#     # Process each PDF file.
#     for file_path in input_files:
#         process_pdf(file_path, args.output, args.names, args.entities, args.coref,
#                     nlp, nlp_coref, stats_list)

#     # Output the stats.
#     if args.stats:
#         try:
#             with open(args.stats, "w", newline="") as csvfile:
#                 writer = csv.writer(csvfile, delimiter="\t")
#                 for record in stats_list:
#                     writer.writerow(record)
#             print(f"Stats written to {args.stats}")
#         except Exception as e:
#             sys.stderr.write(f"Error writing stats file: {e}\n")
#     else:
#         for record in stats_list:
#             sys.stderr.write("\t".join(map(str, record)) + "\n")

# if __name__ == '__main__':
#     main()
#!/usr/bin/env python3
"""
Project 2 - Redacting Statements
CIS 6930 Spring 2025

This script redacts sensitive information from PDF documents based on:
  - A list of case-sensitive names provided via --names
  - Named entities detected by spaCy (by default, only PERSON entities are redacted unless --entities is provided)
  - Coreference tokens redacted via a coreference resolution REST API (if --coref is specified)

Each redaction’s details are logged and output as a tab-separated stats file (or to standard error if not provided).
Usage Example:
    uv run python main.py --input "data/*.pdf" --output myoutput/ --names Bill --names Carter --entities --coref
"""
#!/usr/bin/env python3
"""
Project 2 - Redacting Statements
CIS 6930 Spring 2025

This script redacts sensitive information from PDF documents based on:
  - A list of case-sensitive names provided via --names
  - Named entities detected by spaCy (by default, only PERSON entities are redacted unless --entities is provided)
  - Coreference tokens redacted via a coreference resolution REST API (if --coref is specified)

Each redaction’s details are logged and output as a tab-separated stats file (or to standard error if not provided).
Usage Example:
    uv run python main.py --input "data/*.pdf" --output myoutput/ --names Bill --names Carter --entities --coref
"""
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
    """Send the page text to the coreference resolution API to obtain additional tokens
       that should be redacted; then add redaction annotations for each token returned."""
    text = page.get_text()
    # URL for coreference resolution (as provided; note that the endpoint may be gpu001 to gpu022)
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
