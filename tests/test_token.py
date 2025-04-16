import pytest
import spacy

def test_token():
    nlp = spacy.load("en_core_web_sm")
    doc = nlp("Adam visited NASA.")
    assert len(doc) == 4, "Should produce 4 tokens: Adam / visited / NASA / ."
