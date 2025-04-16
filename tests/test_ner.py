
import subprocess
import pymupdf

def test_ner():
    doc = pymupdf.open('resources/test1in.pdf')
    txt = chr(12).join([p.get_text() for p in doc])
    assert 'Bill' in txt

    subprocess.run(["uv", "run", "python", "main.py", "--input", 'resources/test1in.pdf', "--entities", "--output", "redacted_pdfs", "--stats", "temp.tsv"])

    r_doc = pymupdf.open('redacted_pdfs/test1in.pdf')
    assert 'Bill' not in chr(12).join([p.get_text() for p in r_doc])
