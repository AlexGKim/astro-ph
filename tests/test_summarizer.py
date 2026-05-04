import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import BotoCoreError
from summarizer import summarize_paper


@patch("summarizer.get_bedrock_client")
def test_summarize_paper(mock_get_bedrock_client):
    mock_client = MagicMock()
    mock_get_bedrock_client.return_value = mock_client

    mock_response = {
        "output": {"message": {"content": [{"text": "## Summary\nGood paper."}]}}
    }
    mock_client.converse.return_value = mock_response

    paper_metadata = {"title": "Test Title", "arxiv_id": "123"}
    full_text = "Lots of text"

    summary = summarize_paper(paper_metadata, full_text)

    assert "## Summary" in summary
    mock_client.converse.assert_called_once()


@patch("summarizer.get_bedrock_client")
def test_summarize_paper_error(mock_get_bedrock_client):
    mock_client = MagicMock()
    mock_get_bedrock_client.return_value = mock_client

    mock_client.converse.side_effect = BotoCoreError()

    paper_metadata = {"title": "Test Title", "arxiv_id": "123"}
    full_text = "Lots of text"

    summary = summarize_paper(paper_metadata, full_text)

    assert "**Error:** Could not generate summary" in summary
    assert "Test Title" in summary
