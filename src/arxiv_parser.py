import re
import logging
from typing import List, Dict


def parse_email_text(email_text: str) -> List[Dict[str, str]]:
    """Parses arXiv email text into a list of paper dictionaries."""
    papers = []

    # arXiv emails separate entries with \\
    # We split by \\ and then process chunks
    blocks = email_text.split("\\\\\n")

    for block in blocks:
        if not block.strip() or "astro-ph daily" in block:
            continue

        # Extract ID
        id_match = re.search(r"arXiv:(\d{4}\.\d{4,5})", block)
        if not id_match:
            continue
        arxiv_id = id_match.group(1)

        # Extract Title
        title_match = re.search(r"Title:\s*(.*?)\nAuthors:", block, re.DOTALL)
        if title_match:
            title = re.sub(r"\s+", " ", title_match.group(1).strip())
        else:
            title = ""
            logging.warning(f"Missing Title for arXiv ID: {arxiv_id}")

        # Extract Authors
        authors_match = re.search(r"Authors:\s*(.*?)\nCategories:", block, re.DOTALL)
        if authors_match:
            authors = re.sub(r"\s+", " ", authors_match.group(1).strip())
        else:
            authors = ""
            logging.warning(f"Missing Authors for arXiv ID: {arxiv_id}")

        # Extract Abstract
        # It's usually after Categories and before the closing \\ ( https...
        abstract_match = re.search(
            r"Categories:.*?\n\n(.*?)(?=\\\\ \( https|-----)", block, re.DOTALL
        )
        if abstract_match:
            abstract = re.sub(r"\s+", " ", abstract_match.group(1).strip())
        else:
            abstract = ""
            logging.warning(f"Missing Abstract for arXiv ID: {arxiv_id}")

        papers.append(
            {
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors,
                "abstract": abstract,
            }
        )

    return papers
