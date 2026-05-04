import pytest
import json
from unittest.mock import patch, MagicMock
from llm_filter import filter_papers


@patch("llm_filter.boto3.client")
def test_filter_papers(mock_boto3_client):
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client

    mock_response = {"output": {"message": {"content": [{"text": '["2405.00001"]'}]}}}
    mock_client.converse.return_value = mock_response

    papers = [
        {"arxiv_id": "2405.00001", "title": "SN Ia Paper", "abstract": "Stuff"},
        {"arxiv_id": "2405.00002", "title": "Galaxy Paper", "abstract": "Stuff"},
    ]

    matched_ids = filter_papers(papers)

    assert matched_ids == ["2405.00001"]
    mock_client.converse.assert_called_once()
