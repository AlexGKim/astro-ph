# tests/test_llm_filter.py
import pytest
from unittest.mock import patch, MagicMock
from llm_filter import filter_papers


@patch("llm_filter.OpenAI")
def test_filter_papers(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    # Mock the API response returning a JSON list of IDs
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '["2405.00001"]'
    mock_client.chat.completions.create.return_value = mock_response

    papers = [
        {"arxiv_id": "2405.00001", "title": "SN Ia Paper", "abstract": "Stuff"},
        {"arxiv_id": "2405.00002", "title": "Galaxy Paper", "abstract": "Stuff"},
    ]

    matched_ids = filter_papers(papers, api_key="dummy")

    assert matched_ids == ["2405.00001"]
    mock_client.chat.completions.create.assert_called_once()
