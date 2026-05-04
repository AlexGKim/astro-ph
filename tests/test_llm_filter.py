import pytest
import json
from unittest.mock import patch, MagicMock
from llm_filter import filter_papers, BATCH_SIZE
from botocore.exceptions import ClientError, BotoCoreError


@pytest.fixture
def mock_papers():
    return [
        {"arxiv_id": "2405.00001", "title": "SN Ia Paper", "abstract": "Stuff"},
        {"arxiv_id": "2405.00002", "title": "Galaxy Paper", "abstract": "Stuff"},
    ]


@patch("llm_filter.boto3.client")
def test_filter_papers(mock_boto3_client, mock_papers):
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client

    mock_response = {"output": {"message": {"content": [{"text": '["2405.00001"]'}]}}}
    mock_client.converse.return_value = mock_response

    matched_ids = filter_papers(mock_papers)

    assert matched_ids == ["2405.00001"]
    mock_client.converse.assert_called_once()


@patch("llm_filter.boto3.client")
def test_filter_papers_markdown_stripping(mock_boto3_client, mock_papers):
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client

    # Test markdown block handling
    mock_response = {
        "output": {"message": {"content": [{"text": '```json\n["2405.00002"]\n```'}]}}
    }
    mock_client.converse.return_value = mock_response

    matched_ids = filter_papers(mock_papers)
    assert matched_ids == ["2405.00002"]


@patch("llm_filter.boto3.client")
def test_filter_papers_malformed_json(mock_boto3_client, caplog, mock_papers):
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client

    # Test malformed JSON
    mock_response = {
        "output": {"message": {"content": [{"text": '["2405.00002"'}]}}
    }  # missing closing bracket
    mock_client.converse.return_value = mock_response

    matched_ids = filter_papers(mock_papers)
    assert matched_ids == []
    assert "Error decoding JSON" in caplog.text


@pytest.mark.parametrize(
    "error_instance",
    [
        ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "Converse",
        ),
        BotoCoreError(),
    ],
)
@patch("llm_filter.boto3.client")
def test_filter_papers_bedrock_error(
    mock_boto3_client, caplog, error_instance, mock_papers
):
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client

    mock_client.converse.side_effect = error_instance

    matched_ids = filter_papers(mock_papers)
    assert matched_ids == []
    assert "Bedrock API error" in caplog.text


@patch("llm_filter.boto3.client")
def test_filter_papers_batching(mock_boto3_client):
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client

    mock_response1 = {"output": {"message": {"content": [{"text": '["1"]'}]}}}
    mock_response2 = {"output": {"message": {"content": [{"text": '["21"]'}]}}}

    # Return response1 for first batch, response2 for second batch
    mock_client.converse.side_effect = [mock_response1, mock_response2]

    papers = [
        {"arxiv_id": str(i), "title": f"Paper {i}", "abstract": "Stuff"}
        for i in range(1, BATCH_SIZE + 2)
    ]

    matched_ids = filter_papers(papers)

    # BATCH_SIZE + 1 papers total, -> 2 batches
    assert mock_client.converse.call_count == 2
    assert matched_ids == ["1", "21"]
