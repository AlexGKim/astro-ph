# Bedrock Transition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate LLM calls from OpenAI to Amazon Bedrock using boto3.

**Architecture:** Replace the OpenAI client in `llm_filter.py` and `summarizer.py` with `boto3.client('bedrock-runtime')`. Update the message format to match the Bedrock Converse API standard. Update tests to mock `boto3` instead of `openai`.

**Tech Stack:** Python 3, `boto3`, Amazon Bedrock.

---

### Task 1: Update Dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Replace openai with boto3 in requirements.txt**
```text
google-api-python-client==2.118.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.0
boto3>=1.34.0
arxiv==2.1.0
PyMuPDF==1.23.21
pytest==8.0.2
pytest-mock==3.12.0
python-dotenv==1.0.1
```

- [ ] **Step 2: Commit**
```bash
git add requirements.txt
git commit -m "chore: replace openai with boto3"
```

### Task 2: Refactor LLM Filter

**Files:**
- Modify: `src/llm_filter.py`
- Modify: `tests/test_llm_filter.py`

- [ ] **Step 1: Update test_llm_filter.py**
```python
import pytest
import json
from unittest.mock import patch, MagicMock
from llm_filter import filter_papers

@patch('llm_filter.boto3.client')
def test_filter_papers(mock_boto3_client):
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client
    
    mock_response = {
        'output': {
            'message': {
                'content': [{'text': '["2405.00001"]'}]
            }
        }
    }
    mock_client.converse.return_value = mock_response
    
    papers = [
        {'arxiv_id': '2405.00001', 'title': 'SN Ia Paper', 'abstract': 'Stuff'},
        {'arxiv_id': '2405.00002', 'title': 'Galaxy Paper', 'abstract': 'Stuff'}
    ]
    
    matched_ids = filter_papers(papers)
    
    assert matched_ids == ["2405.00001"]
    mock_client.converse.assert_called_once()
```

- [ ] **Step 2: Update llm_filter.py**
```python
import json
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

INTERESTS = """
- Supernova Cosmology
- Type Ia Supernovae
- Cosmological Constraints
- Bayesian Inference in Cosmology
- Time-Domain Astronomy (LSST, DECam)
- Dark Energy Survey (DES)
- Gravitational Lensing
- Peculiar Velocities
- Intensity Interferometry
- Precision Probes of Cosmology
- Hanbury Brown and Twiss
"""


def filter_papers(papers, model="anthropic.claude-3-haiku-20240307-v1:0"):
    """Uses LLM to filter papers. Returns list of matched arXiv IDs."""
    if not papers:
        return []

    client = boto3.client('bedrock-runtime')
    all_matched_ids = []

    # Process papers in batches of 20 to avoid context limits
    batch_size = 20
    for i in range(0, len(papers), batch_size):
        batch = papers[i : i + batch_size]

        prompt = f"""
        You are an expert astrophysicist evaluating papers for a researcher.
        The researcher's interests are:
        {INTERESTS}
        
        Here is a list of papers from today's astro-ph:
        """

        for p in batch:
            prompt += f"\nID: {p['arxiv_id']}\nTitle: {p['title']}\nAbstract: {p['abstract']}\n"

        prompt += """
        Based on the titles and abstracts, identify which papers align closely with the researcher's interests.
        Return ONLY a JSON array of the matching ID strings.
        Example: ["2405.00001", "2405.00003"]
        """

        content = ""
        try:
            response = client.converse(
                modelId=model,
                messages=[
                    {"role": "user", "content": [{"text": prompt}]},
                ],
                system=[{"text": "You output JSON arrays of strings."}],
                inferenceConfig={"temperature": 0.0}
            )

            content = response['output']['message']['content'][0]['text'].strip()

            # Handle markdown code blocks if the LLM adds them
            if content.startswith("```"):
                content = content.strip("`").removeprefix("json").strip()

            matched_ids = json.loads(content)
            all_matched_ids.extend(matched_ids)

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Bedrock API error: {e}")
            continue
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON: {content}")
            continue

    return all_matched_ids
```

- [ ] **Step 3: Run tests**
```bash
pytest tests/test_llm_filter.py -v
```
Expected: PASS

- [ ] **Step 4: Commit**
```bash
git add src/llm_filter.py tests/test_llm_filter.py
git commit -m "feat: migrate llm_filter to bedrock"
```

### Task 3: Refactor Summarizer

**Files:**
- Modify: `src/summarizer.py`
- Modify: `tests/test_summarizer.py`

- [ ] **Step 1: Update test_summarizer.py**
```python
import pytest
from unittest.mock import patch, MagicMock
from summarizer import summarize_paper

@patch('summarizer.boto3.client')
def test_summarize_paper(mock_boto3_client):
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client
    
    mock_response = {
        'output': {
            'message': {
                'content': [{'text': '## Summary\nGood paper.'}]
            }
        }
    }
    mock_client.converse.return_value = mock_response
    
    paper_metadata = {'title': 'Test Title', 'arxiv_id': '123'}
    full_text = "Lots of text"
    
    summary = summarize_paper(paper_metadata, full_text)
    
    assert "## Summary" in summary
    mock_client.converse.assert_called_once()
```

- [ ] **Step 2: Update summarizer.py**
```python
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError


def summarize_paper(paper_metadata, full_text, model="anthropic.claude-3-5-sonnet-20240620-v1:0"):
    """Sends full text to LLM for a structured summary."""
    client = boto3.client('bedrock-runtime')

    # Truncate text if it's absurdly long
    # 100,000 chars is usually safe for a paper
    safe_text = full_text[:100000]

    prompt = f"""
    You are an expert astrophysicist summarizing a paper for a colleague.
    
    Title: {paper_metadata["title"]}
    arXiv ID: {paper_metadata["arxiv_id"]}
    
    Please read the following text extracted from the PDF and provide a structured summary in Markdown format exactly as follows:
    
    ## [{paper_metadata["title"]}](https://arxiv.org/abs/{paper_metadata["arxiv_id"]})
    **Authors:** {paper_metadata.get("authors", "Unknown")}

    **The Gist (1-2 sentences):**
    [High-level summary of achievement and relevance]

    **Key Methodology:**
    [How the research was conducted]

    **Main Findings:**
    - [Result 1]
    - [Result 2]

    **Limitations / Caveats (if mentioned):**
    [Author-stated limitations or assumptions]
    
    Paper Text:
    {safe_text}
    """

    try:
        response = client.converse(
            modelId=model,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.3}
        )
        content = response['output']['message']['content'][0]['text']
        return content.strip() if content else ""
    except (BotoCoreError, ClientError) as e:
        logging.error(f"Bedrock API error during summarization: {e}")
        return f"## [{paper_metadata['title']}](https://arxiv.org/abs/{paper_metadata['arxiv_id']})\n\n**Error:** Could not generate summary due to API error."
    except Exception as e:
        logging.error(f"Unexpected error during summarization: {e}")
        return f"## [{paper_metadata['title']}](https://arxiv.org/abs/{paper_metadata['arxiv_id']})\n\n**Error:** Could not generate summary due to an unexpected error."
```

- [ ] **Step 3: Run tests**
```bash
pytest tests/test_summarizer.py -v
```
Expected: PASS

- [ ] **Step 4: Commit**
```bash
git add src/summarizer.py tests/test_summarizer.py
git commit -m "feat: migrate summarizer to bedrock"
```

### Task 4: Cleanup Main Orchestrator

**Files:**
- Modify: `src/main.py`
- Modify: `tests/test_main.py`

- [ ] **Step 1: Update test_main.py**
```python
import pytest
import sys
import logging
from unittest.mock import patch, MagicMock
from main import main

@patch("main.get_gmail_service")
@patch("main.fetch_latest_astroph_email")
@patch("main.argparse.ArgumentParser.parse_args")
def test_main_no_emails(
    mock_parse_args, mock_fetch, mock_get_gmail, caplog
):
    mock_parse_args.return_value = MagicMock(
        dry_run=True, no_mark_read=True, email="test@example.com"
    )
    mock_fetch.return_value = None

    with caplog.at_level(logging.INFO):
        with patch.object(sys, "argv", ["main.py", "--email", "test@example.com"]):
            main()

    assert "No unread astro-ph emails found" in caplog.text


@patch("main.get_gmail_service")
@patch("main.fetch_latest_astroph_email")
@patch("main.parse_email_text")
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
    mock_parse,
    mock_fetch,
    mock_get_gmail,
):
    mock_parse_args.return_value = MagicMock(
        dry_run=False, no_mark_read=False, email="test@example.com"
    )
    mock_fetch.return_value = "raw email content"
    mock_parse.return_value = [
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

@patch('main.get_gmail_service')
@patch('main.fetch_latest_astroph_email')
@patch('main.parse_email_text')
@patch('main.filter_papers')
@patch('main.argparse.ArgumentParser.parse_args')
def test_main_no_matched_papers(mock_parse_args, mock_filter, mock_parse, mock_fetch, mock_get_gmail, caplog):
    mock_parse_args.return_value = MagicMock(dry_run=True, no_mark_read=True, email="test@example.com")
    mock_fetch.return_value = "raw email content"
    mock_parse.return_value = [{'arxiv_id': '123', 'title': 'Test Paper', 'abstract': 'Stuff'}]
    mock_filter.return_value = []
    
    with caplog.at_level(logging.INFO):
        with patch.object(sys, 'argv', ['main.py', '--email', 'test@example.com']):
            main()
            
    assert "No papers matched interests today" in caplog.text

@patch('main.get_gmail_service')
@patch('main.fetch_latest_astroph_email')
@patch('main.parse_email_text')
@patch('main.argparse.ArgumentParser.parse_args')
def test_main_no_valid_papers(mock_parse_args, mock_parse, mock_fetch, mock_get_gmail, caplog):
    mock_parse_args.return_value = MagicMock(dry_run=True, no_mark_read=True, email="test@example.com")
    mock_fetch.return_value = "raw email content"
    mock_parse.return_value = []
    
    with caplog.at_level(logging.INFO):
        with patch.object(sys, 'argv', ['main.py', '--email', 'test@example.com']):
            main()
            
    assert "No valid papers found to parse" in caplog.text
```

- [ ] **Step 2: Update main.py**
Remove references to `api_key`.
```python
import os
import argparse
import logging
from dotenv import load_dotenv
from email_client import get_gmail_service, fetch_latest_astroph_email, send_email
from arxiv_parser import parse_email_text
from llm_filter import filter_papers
from pdf_processor import download_and_extract_text
from summarizer import summarize_paper

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Astro-ph Daily Summarizer")
    parser.add_argument("--dry-run", action="store_true", help="Process but don't send final email")
    parser.add_argument("--no-mark-read", action="store_true", help="Don't mark the arxiv email as read")
    parser.add_argument("--email", type=str, required=True, help="Email address to send results to")
    args = parser.parse_args()

    logging.info("Authenticating with Gmail...")
    try:
        service = get_gmail_service()
    except Exception as e:
        logging.error(f"Failed to authenticate with Gmail: {e}")
        return

    logging.info("Fetching latest astro-ph email...")
    mark_read = not args.no_mark_read
    email_text = fetch_latest_astroph_email(service, mark_read=mark_read)
    
    if not email_text:
        logging.info("No unread astro-ph emails found.")
        return
        
    logging.info("Parsing email...")
    papers = parse_email_text(email_text)
    
    if not papers:
        logging.info("No valid papers found to parse.")
        return
        
    logging.info(f"Found {len(papers)} papers in email.")

    logging.info("Filtering papers with LLM...")
    matched_ids = filter_papers(papers)
    logging.info(f"Found {len(matched_ids)} matching papers: {matched_ids}")
    
    if not matched_ids:
        logging.info("No papers matched interests today.")
        return

    # Create a lookup dict for matched papers
    matched_papers = [p for p in papers if p['arxiv_id'] in matched_ids]
    
    summaries = []
    for paper in matched_papers:
        logging.info(f"Processing PDF for {paper['arxiv_id']}...")
        full_text = download_and_extract_text(paper['arxiv_id'])
        
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
        result = send_email(service, args.email, "Your Astro-ph Daily Summary", final_report)
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
git commit -m "feat: remove openai api key dependency from main"
```
