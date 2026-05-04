import pytest
import pathlib
from arxiv_parser import parse_email_text


def test_parse_email_text():
    data_path = pathlib.Path(__file__).parent / "data" / "sample_email.txt"
    with open(data_path, "r", encoding="utf-8") as f:
        text = f.read()

    papers = parse_email_text(text)

    assert len(papers) == 2
    assert papers[0]["arxiv_id"] == "2405.00001"
    assert papers[0]["title"] == "A Cool Supernova Paper"
    assert papers[0]["authors"] == "First Author, Second Author"
    assert "cool paper" in papers[0]["abstract"]
    assert papers[1]["arxiv_id"] == "2405.00002"
