# ArXiv API Transition Design

## Overview
Replace the Gmail-based email parser with a direct fetch from the arXiv API using the `arxiv` python package. This improves reliability and completely decouples the ingestion step from Gmail, while retaining Gmail for the final delivery.

## Changes
1. **New Module:** `src/arxiv_fetcher.py`.
   - Function: `fetch_daily_astroph_papers()`
   - Logic: Uses `arxiv.Search` with `query="cat:astro-ph"`, `sort_by=arxiv.SortCriterion.SubmittedDate`, `sort_order=arxiv.SortOrder.Descending`.
   - Logic: Fetches papers and filters them locally to only include those submitted within the last 24 hours from the time of execution.
   - Returns: List of dictionaries matching the current format `{'arxiv_id': id, 'title': title, 'abstract': abstract, 'authors': authors}`.
2. **Remove Outdated Code:**
   - Remove `fetch_latest_astroph_email` from `src/email_client.py`.
   - Remove `src/arxiv_parser.py` completely.
   - Remove associated tests.
3. **Refactor Orchestrator:**
   - Update `main.py` to call `fetch_daily_astroph_papers()` instead of fetching/parsing emails.
   - Remove `--no-mark-read` CLI argument as it is no longer relevant.
