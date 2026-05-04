import pytest
import os
from unittest.mock import patch, MagicMock
from pdf_processor import download_and_extract_text


@patch("pdf_processor.arxiv.Client")
@patch("pdf_processor.fitz.open")
@patch("pdf_processor.os.remove")
def test_download_and_extract_text(mock_remove, mock_fitz_open, mock_arxiv_client):
    # Mock arXiv client and paper download
    mock_paper = MagicMock()
    mock_paper.download_pdf.return_value = "dummy.pdf"

    mock_search = MagicMock()
    mock_search.results.return_value = [mock_paper]
    mock_arxiv_client.return_value.results.return_value = [mock_paper]

    # Mock PDF extraction
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = "PDF text content"
    mock_doc.__iter__.return_value = [mock_page]
    mock_fitz_open.return_value.__enter__.return_value = mock_doc

    text = download_and_extract_text("2405.00001")

    assert text == "PDF text content"
    mock_paper.download_pdf.assert_called_once()
    mock_remove.assert_called_once_with("dummy.pdf")
