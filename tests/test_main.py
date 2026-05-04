import pytest
import sys
from unittest.mock import patch, MagicMock
from main import main


@patch("main.os.environ.get")
@patch("main.argparse.ArgumentParser.parse_args")
def test_main_no_api_key(mock_parse_args, mock_get_env, capsys):
    mock_parse_args.return_value = MagicMock(
        dry_run=True, no_mark_read=True, email="test@example.com"
    )
    mock_get_env.return_value = None

    with patch.object(sys, "argv", ["main.py", "--email", "test@example.com"]):
        main()

    captured = capsys.readouterr()
    assert "Error: OPENAI_API_KEY not set" in captured.out


@patch("main.get_gmail_service")
@patch("main.fetch_latest_astroph_email")
@patch("main.os.environ.get")
@patch("main.argparse.ArgumentParser.parse_args")
def test_main_no_emails(
    mock_parse_args, mock_get_env, mock_fetch, mock_get_gmail, capsys
):
    mock_parse_args.return_value = MagicMock(
        dry_run=True, no_mark_read=True, email="test@example.com"
    )
    mock_get_env.return_value = "dummy_key"
    mock_fetch.return_value = None

    with patch.object(sys, "argv", ["main.py", "--email", "test@example.com"]):
        main()

    captured = capsys.readouterr()
    assert "No unread astro-ph emails found" in captured.out


@patch("main.get_gmail_service")
@patch("main.fetch_latest_astroph_email")
@patch("main.parse_email_text")
@patch("main.filter_papers")
@patch("main.download_and_extract_text")
@patch("main.summarize_paper")
@patch("main.send_email")
@patch("main.os.environ.get")
@patch("main.argparse.ArgumentParser.parse_args")
def test_main_happy_path(
    mock_parse_args,
    mock_get_env,
    mock_send,
    mock_summarize,
    mock_download,
    mock_filter,
    mock_parse,
    mock_fetch,
    mock_get_gmail,
    capsys,
):
    mock_parse_args.return_value = MagicMock(
        dry_run=False, no_mark_read=False, email="test@example.com"
    )
    mock_get_env.return_value = "dummy_key"
    mock_fetch.return_value = "raw email content"
    mock_parse.return_value = [
        {"arxiv_id": "123", "title": "Test Paper", "abstract": "Stuff"}
    ]
    mock_filter.return_value = ["123"]
    mock_download.return_value = "Extracted PDF text"
    mock_summarize.return_value = "## Summary"

    with patch.object(sys, "argv", ["main.py", "--email", "test@example.com"]):
        main()

    mock_send.assert_called_once()
    args = mock_send.call_args[0]
    assert args[1] == "test@example.com"
    assert "## Summary" in args[3]
