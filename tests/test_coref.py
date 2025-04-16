import pytest
import spacy
import spacy_experimental

def test_coref():
    try:
        coref_nlp = spacy.load("en_coreference_web_trf")
    except:
        pytest.skip("Coref model not installed.")

    text = "Rick saw the UFO. He said it was very large."
    doc = coref_nlp(text)
    clusters = doc.spans
    assert len(clusters) > 0, "Should find at least one cluster for 'Rick' and 'He'."
