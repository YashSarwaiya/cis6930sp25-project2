# cis6930sp25 -- Project 2: Redacting Statements

**Name:** Yash Sarwaiya  
**Gator Email:** yashsarwaiya@ufl.edu

---

## Assignment Description

This project redacts sensitive information from PDF documents including names, named entities (NER), and coreferent phrases. The redactor uses:

- User-supplied names via `--names`
- Named Entity Recognition (NER) via spaCy
- Coreference Resolution via a REST API

Redacted files are saved in the output folder and statistics of redactions are saved in a `.tsv` file.

---

## Setup & Installing Models

```bash
# Create project folder and initialize environment
uv python pin 3.10
uv init .
uv venv
source .venv/bin/activate

# Add dependencies
uv add --no-cache pip setuptools wheel
uv add pymupdf requests tqdm
uv pip install https://github.com/explosion/spacy-experimental/releases/download/v0.6.1/en_coreference_web_trf-3.4.0a2-py3-none-any.whl

uv run -m spacy download en_core_web_sm
uv run -m spacy download en_core_web_trf
```

---

## How to Run

### Run Tests

```bash
uv run python -m pytest -v
```

### Redact with names and entities:

```bash
uv run python main.py   --input "tests/test1in.pdf"   --output redacted_pdfs   --names "Bill Carter" "Rick Scott"   --entities   --stats redacted_pdfs/stats.tsv
```

### Redact with coreference (requires UF CM cluster):

```bash
uv run python main.py   --input "tests/test1in.pdf"   --output redacted_pdfs   --coref   --stats redacted_pdfs/stats.tsv
```

---

## Example Folder Structure

```
cis6930sp25-project2/
├── main.py
├── pyproject.toml
├── README.md
├── COLLABORATORS.md
├── tests/
│   ├── test_coref.pdf
│   ├── test_ner.pdf
│   └── test_token.pdf
├── redacted_pdfs/
│   └── test1in.pdf
└── .python-version
```

---

## Example Stats Output (`stats.tsv`)

```
test1in.pdf	0:100x200	Rick Scott	10	Name
test1in.pdf	0:130x240	Scott	5	Entity
test1in.pdf	0:150x260	He	2	Coref
```

---

## Features and Functions

### `main.py`

- Parses CLI arguments
- Uses PyMuPDF to redact text on pages
- Uses spaCy for NER
- Calls external API for coreference resolution
- Records and writes stats in TSV format

---

## Bugs and Assumptions

- Coreference resolution only works **on the UF internal network**. On local machines, it fails due to hostname resolution error.
- spaCy entity detection may miss edge cases if tokenization fails on complex punctuation.
- Names are case-sensitive and must match exactly.
- Redactions are based on text-level matches, and not fuzzy-matched.

---
