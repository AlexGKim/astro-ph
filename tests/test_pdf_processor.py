import pytest
import os
from unittest.mock import patch, MagicMock, ANY
from pdf_processor import download_and_extract_text


@patch("pdf_processor.arxiv.Client")
@patch("pdf_processor.fitz.open")
@patch("pdf_processor.os.remove")
@patch("pdf_processor.os.path.exists")
@patch("pdf_processor.tempfile.mkstemp")
def test_download_and_extract_text(
    mock_mkstemp, mock_exists, mock_remove, mock_fitz_open, mock_arxiv_client
):
    mock_exists.return_value = True
    mock_mkstemp.return_value = (123, "/tmp/dummy.pdf")

    # Mock arXiv client and paper download
    mock_paper = MagicMock()
    mock_paper.download_pdf.return_value = None

    # client.results(search) returns an iterator
    mock_arxiv_client.return_value.results.return_value = iter([mock_paper])

    # Mock PDF extraction
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = "PDF text content"
    mock_doc.__iter__.return_value = [mock_page]
    mock_fitz_open.return_value.__enter__.return_value = mock_doc

    with patch("pdf_processor.os.close") as mock_close:
        text = download_and_extract_text("2405.00001")

    assert text == "PDF text content"
    mock_close.assert_called_once_with(123)
    mock_paper.download_pdf.assert_called_once_with(filename="/tmp/dummy.pdf")
    mock_remove.assert_called_once_with("/tmp/dummy.pdf")


@patch("pdf_processor.arxiv.Client")
@patch("pdf_processor.tempfile.mkstemp")
def test_download_and_extract_text_exception(mock_mkstemp, mock_arxiv_client):
    mock_mkstemp.return_value = (123, "/tmp/dummy.pdf")

    mock_paper = MagicMock()
    mock_paper.download_pdf.side_effect = Exception("Download failed")
    mock_arxiv_client.return_value.results.return_value = iter([mock_paper])

    with (
        patch("pdf_processor.os.close") as mock_close,
        patch("pdf_processor.os.path.exists", return_value=True),
        patch("pdf_processor.os.remove") as mock_remove,
    ):
        text = download_and_extract_text("2405.00001")

    assert text == ""
    mock_close.assert_called_once_with(123)
    mock_remove.assert_called_once_with("/tmp/dummy.pdf")
