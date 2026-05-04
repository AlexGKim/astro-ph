import pytest
from unittest.mock import patch, MagicMock
from openai import OpenAIError
from summarizer import summarize_paper


@patch("summarizer.OpenAI")
def test_summarize_paper(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "## Summary\nGood paper."
    mock_client.chat.completions.create.return_value = mock_response

    paper_metadata = {"title": "Test Title", "arxiv_id": "123"}
    full_text = "Lots of text"

    summary = summarize_paper(paper_metadata, full_text, api_key="dummy")

    assert "## Summary" in summary
    mock_client.chat.completions.create.assert_called_once()


@patch("summarizer.OpenAI")
def test_summarize_paper_error(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    mock_client.chat.completions.create.side_effect = OpenAIError("API down")

    paper_metadata = {"title": "Test Title", "arxiv_id": "123"}
    full_text = "Lots of text"

    summary = summarize_paper(paper_metadata, full_text, api_key="dummy")

    assert "**Error:** Could not generate summary" in summary
    assert "Test Title" in summary
