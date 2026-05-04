# tests/test_llm_filter.py
import pytest
import json
import openai
from unittest.mock import patch, MagicMock
from llm_filter import filter_papers


@patch("llm_filter.OpenAI")
def test_filter_papers_happy_path(mock_openai):
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


@patch("llm_filter.OpenAI")
def test_filter_papers_markdown_stripping(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    mock_response = MagicMock()
    # Test markdown block handling
    mock_response.choices[0].message.content = '```json\n["2405.00002"]\n```'
    mock_client.chat.completions.create.return_value = mock_response

    papers = [
        {"arxiv_id": "2405.00002", "title": "Galaxy Paper", "abstract": "Stuff"},
    ]

    matched_ids = filter_papers(papers, api_key="dummy")
    assert matched_ids == ["2405.00002"]


@patch("llm_filter.OpenAI")
def test_filter_papers_malformed_json(mock_openai, caplog):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    mock_response = MagicMock()
    # Test malformed JSON
    mock_response.choices[
        0
    ].message.content = '["2405.00002"'  # missing closing bracket
    mock_client.chat.completions.create.return_value = mock_response

    papers = [
        {"arxiv_id": "2405.00002", "title": "Galaxy Paper", "abstract": "Stuff"},
    ]

    matched_ids = filter_papers(papers, api_key="dummy")
    assert matched_ids == []
    assert "Error decoding JSON" in caplog.text


@patch("llm_filter.OpenAI")
def test_filter_papers_openai_error(mock_openai, caplog):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    # Test OpenAIError
    mock_client.chat.completions.create.side_effect = openai.OpenAIError(
        "API rate limit exceeded"
    )

    papers = [
        {"arxiv_id": "2405.00002", "title": "Galaxy Paper", "abstract": "Stuff"},
    ]

    matched_ids = filter_papers(papers, api_key="dummy")
    assert matched_ids == []
    assert "OpenAI API error" in caplog.text


@patch("llm_filter.OpenAI")
def test_filter_papers_batching(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    mock_response1 = MagicMock()
    mock_response1.choices[0].message.content = '["1"]'

    mock_response2 = MagicMock()
    mock_response2.choices[0].message.content = '["21"]'

    # Return response1 for first batch, response2 for second batch
    mock_client.chat.completions.create.side_effect = [mock_response1, mock_response2]

    papers = [
        {"arxiv_id": str(i), "title": f"Paper {i}", "abstract": "Stuff"}
        for i in range(1, 22)
    ]

    matched_ids = filter_papers(papers, api_key="dummy")

    # 21 papers total, batch size is 20 -> 2 batches
    assert mock_client.chat.completions.create.call_count == 2
    assert matched_ids == ["1", "21"]
