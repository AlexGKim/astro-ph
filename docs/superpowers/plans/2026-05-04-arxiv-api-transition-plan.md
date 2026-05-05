# ArXiv API Transition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fetch daily papers directly from the arXiv API instead of parsing the daily email digest.

**Architecture:** Create a new `arxiv_fetcher.py` module to query the arXiv API using the `arxiv` python package for `cat:astro-ph` papers submitted in the last 24 hours. Delete the old email parsing code and update `main.py` to use the new fetcher.

**Tech Stack:** Python 3, `arxiv`.

---

### Task 1: Create ArXiv Fetcher

**Files:**
- Create: `src/arxiv_fetcher.py`
- Create: `tests/test_arxiv_fetcher.py`

- [ ] **Step 1: Write the failing tests**
```python
# tests/test_arxiv_fetcher.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from arxiv_fetcher import fetch_daily_astroph_papers

@patch('arxiv_fetcher.arxiv.Client')
@patch('arxiv_fetcher.arxiv.Search')
def test_fetch_daily_astroph_papers(mock_search, mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    now = datetime.now(timezone.utc)
    
    # Create mock papers
    paper1 = MagicMock()
    paper1.get_short_id.return_value = "2405.00001"
    paper1.title = "Recent Paper"
    paper1.summary = "Recent abstract"
    author1 = MagicMock(); author1.name = "Author One"
    paper1.authors = [author1]
    paper1.published = now - timedelta(hours=12) # Inside 24h
    
    paper2 = MagicMock()
    paper2.get_short_id.return_value = "2405.00002"
    paper2.title = "Old Paper"
    paper2.summary = "Old abstract"
    paper2.authors = []
    paper2.published = now - timedelta(hours=48) # Outside 24h
    
    mock_client.results.return_value = [paper1, paper2]
    
    results = fetch_daily_astroph_papers()
    
    assert len(results) == 1
    assert results[0]['arxiv_id'] == "2405.00001"
    assert results[0]['title'] == "Recent Paper"
    assert results[0]['abstract'] == "Recent abstract"
    assert results[0]['authors'] == "Author One"
```

- [ ] **Step 2: Run test to verify failure**
```bash
pytest tests/test_arxiv_fetcher.py -v
```
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Write implementation**
```python
# src/arxiv_fetcher.py
import arxiv
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

def fetch_daily_astroph_papers():
    """
    Fetches papers from the astro-ph category submitted within the last 24 hours.
    Returns a list of dictionaries matching the legacy email parser format.
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query="cat:astro-ph",
        max_results=100,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    papers = []
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(hours=24)
    
    try:
        results = client.results(search)
        for paper in results:
            # Stop processing if we hit papers older than 24 hours
            # (Since they are sorted descending by date)
            if paper.published < cutoff_time:
                break
                
            papers.append({
                'arxiv_id': paper.get_short_id(),
                'title': paper.title.replace('\n', ' '),
                'abstract': paper.summary.replace('\n', ' '),
                'authors': ', '.join([author.name for author in paper.authors])
            })
            
        return papers
    except Exception as e:
        logger.error(f"Failed to fetch papers from arXiv API: {e}")
        return []
```

- [ ] **Step 4: Run test to verify success**
```bash
pytest tests/test_arxiv_fetcher.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/arxiv_fetcher.py tests/test_arxiv_fetcher.py
git commit -m "feat: add arxiv api fetcher"
```

### Task 2: Remove Obsolete Email Parsing Code

**Files:**
- Delete: `src/arxiv_parser.py`
- Delete: `tests/test_arxiv_parser.py`
- Modify: `src/email_client.py`
- Modify: `tests/test_email_client.py`

- [ ] **Step 1: Delete parsing files**
```bash
rm src/arxiv_parser.py tests/test_arxiv_parser.py
```

- [ ] **Step 2: Update email_client.py**
Remove `fetch_latest_astroph_email` function and the `import base64` statement if it's unused elsewhere. (Keep `get_gmail_service` and `send_email`).

- [ ] **Step 3: Update test_email_client.py**
Remove `test_fetch_latest_astroph_email` and `test_fetch_latest_astroph_email_no_messages`. Keep `test_get_gmail_service_with_existing_token` and `test_send_email`.

- [ ] **Step 4: Run remaining tests**
```bash
pytest tests/test_email_client.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add -u
git commit -m "refactor: remove obsolete email fetching and parsing code"
```

### Task 3: Update Main Orchestrator

**Files:**
- Modify: `src/main.py`
- Modify: `tests/test_main.py`

- [ ] **Step 1: Update test_main.py**
Rewrite the tests to mock `fetch_daily_astroph_papers` instead of `fetch_latest_astroph_email` and `parse_email_text`. Remove the `--no-mark-read` mock arguments.

```python
# tests/test_main.py
import pytest
import sys
import logging
from unittest.mock import patch, MagicMock
from main import main

@patch("main.fetch_daily_astroph_papers")
@patch("main.argparse.ArgumentParser.parse_args")
def test_main_no_papers_found(mock_parse_args, mock_fetch, caplog):
    mock_parse_args.return_value = MagicMock(dry_run=True, email="test@example.com")
    mock_fetch.return_value = []

    with caplog.at_level(logging.INFO):
        with patch.object(sys, "argv", ["main.py", "--email", "test@example.com"]):
            main()

    assert "No recent astro-ph papers found." in caplog.text


@patch("main.get_gmail_service")
@patch("main.fetch_daily_astroph_papers")
@patch("main.filter_papers")
@patch("main.download_and_extract_text")
@patch("main.summarize_paper")
@patch("main.send_email")
@patch("main.argparse.ArgumentParser.parse_args")
def test_main_happy_path(
    mock_parse_args,
    mock_send,
    mock_summarize,
    mock_download,
    mock_filter,
    mock_fetch,
    mock_get_gmail,
):
    mock_parse_args.return_value = MagicMock(dry_run=False, email="test@example.com")
    mock_fetch.return_value = [
        {"arxiv_id": "123", "title": "Test Paper", "abstract": "Stuff"}
    ]
    mock_filter.return_value = ["123"]
    mock_download.return_value = "Extracted PDF text"
    mock_summarize.return_value = "## Summary"
    mock_send.return_value = True

    with patch.object(sys, "argv", ["main.py", "--email", "test@example.com"]):
        main()

    mock_send.assert_called_once()
    args = mock_send.call_args[0]
    assert args[1] == "test@example.com"
    assert "## Summary" in args[3]

@patch("main.get_gmail_service")
@patch("main.argparse.ArgumentParser.parse_args")
def test_main_gmail_auth_failure(mock_parse_args, mock_get_gmail, caplog):
    mock_parse_args.return_value = MagicMock(dry_run=False, email="test@example.com")
    mock_get_gmail.side_effect = Exception("Credentials not found")

    with caplog.at_level(logging.ERROR):
        with patch.object(sys, "argv", ["main.py", "--email", "test@example.com"]):
            main()

    assert "Gmail authentication failed" in caplog.text
```

- [ ] **Step 2: Update main.py**
```python
# src/main.py
import argparse
import logging
from dotenv import load_dotenv
from email_client import get_gmail_service, send_email
from arxiv_fetcher import fetch_daily_astroph_papers
from llm_filter import filter_papers
from pdf_processor import download_and_extract_text
from summarizer import summarize_paper

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Astro-ph Daily Summarizer")
    parser.add_argument(
        "--dry-run", action="store_true", help="Process but don't send final email"
    )
    parser.add_argument(
        "--email", type=str, required=True, help="Email address to send results to"
    )
    args = parser.parse_args()

    # If we are actually sending an email, authenticate early to fail fast
    service = None
    if not args.dry_run:
        logging.info("Authenticating with Gmail for delivery...")
        try:
            service = get_gmail_service()
        except Exception as e:
            logging.error(f"Gmail authentication failed: {e}")
            return

    logging.info("Fetching latest astro-ph papers from arXiv API...")
    papers = fetch_daily_astroph_papers()

    if not papers:
        logging.info("No recent astro-ph papers found.")
        return

    logging.info(f"Found {len(papers)} papers from the last 24 hours.")

    logging.info("Filtering papers with LLM...")
    matched_ids = filter_papers(papers)
    logging.info(f"Found {len(matched_ids)} matching papers: {matched_ids}")

    if not matched_ids:
        logging.info("No papers matched interests today.")
        return

    # Create a list of matched papers
    matched_papers = [p for p in papers if p["arxiv_id"] in matched_ids]

    summaries = []
    for paper in matched_papers:
        logging.info(f"Processing PDF for {paper['arxiv_id']}...")
        full_text = download_and_extract_text(paper["arxiv_id"])

        if not full_text:
            logging.warning(f"Could not extract text for {paper['arxiv_id']}")
            continue

        logging.info(f"Summarizing {paper['arxiv_id']}...")
        summary = summarize_paper(paper, full_text)
        summaries.append(summary)

    if not summaries:
        logging.info("No summaries generated.")
        return

    final_report = "# Astro-ph Daily Summary\n\n" + "\n\n---\n\n".join(summaries)

    if args.dry_run:
        logging.info("\n--- DRY RUN OUTPUT ---\n")
        print(final_report)
    else:
        logging.info(f"Sending email to {args.email}...")
        result = send_email(
            service, args.email, "Your Astro-ph Daily Summary", final_report
        )
        if result:
            logging.info("Email sent successfully!")
        else:
            logging.error("Failed to send email.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run all tests**
```bash
pytest -v
```
Expected: PASS

- [ ] **Step 4: Commit**
```bash
git add src/main.py tests/test_main.py
git commit -m "feat: use arxiv api fetcher in main orchestrator"
```
