import arxiv
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def fetch_daily_astroph_papers(debug=False):
    """
    Fetches papers from the astro-ph category submitted within the last 24 hours (or 7 days in debug mode).
    Returns a list of dictionaries matching the legacy email parser format.
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query="cat:astro-ph*",
        max_results=None if debug else 100,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers = []
    now = datetime.now(timezone.utc)

    if debug:
        cutoff_time = now - timedelta(days=7)
    else:
        cutoff_time = now - timedelta(hours=24)

    try:
        results = client.results(search)
        for paper in results:
            # Stop processing if we hit papers older than 24 hours
            # (Since they are sorted descending by date)
            if paper.published < cutoff_time:
                break

            papers.append(
                {
                    "arxiv_id": paper.get_short_id(),
                    "title": paper.title.replace("\n", " "),
                    "abstract": paper.summary.replace("\n", " "),
                    "authors": ", ".join([author.name for author in paper.authors]),
                }
            )

        return papers
    except Exception as e:
        logger.error(f"Failed to fetch papers from arXiv API: {e}")
        return []
