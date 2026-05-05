import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from arxiv_fetcher import fetch_daily_astroph_papers


@patch("arxiv_fetcher.arxiv.Client")
@patch("arxiv_fetcher.arxiv.Search")
def test_fetch_daily_astroph_papers(mock_search, mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    now = datetime.now(timezone.utc)

    # Create mock papers
    paper1 = MagicMock()
    paper1.get_short_id.return_value = "2405.00001"
    paper1.title = "Recent Paper"
    paper1.summary = "Recent abstract"
    author1 = MagicMock()
    author1.name = "Author One"
    paper1.authors = [author1]
    paper1.published = now - timedelta(hours=12)  # Inside 24h

    paper2 = MagicMock()
    paper2.get_short_id.return_value = "2405.00002"
    paper2.title = "Old Paper"
    paper2.summary = "Old abstract"
    paper2.authors = []
    paper2.published = now - timedelta(hours=48)  # Outside 24h

    mock_client.results.return_value = [paper1, paper2]

    results = fetch_daily_astroph_papers()

    assert len(results) == 1
    assert results[0]["arxiv_id"] == "2405.00001"
    assert results[0]["title"] == "Recent Paper"
    assert results[0]["abstract"] == "Recent abstract"
    assert results[0]["authors"] == "Author One"
