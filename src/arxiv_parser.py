import re


def parse_email_text(email_text):
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
        title = title_match.group(1).strip().replace("\n ", " ") if title_match else ""

        # Extract Authors
        authors_match = re.search(r"Authors:\s*(.*?)\nCategories:", block, re.DOTALL)
        authors = (
            authors_match.group(1).strip().replace("\n ", " ") if authors_match else ""
        )

        # Extract Abstract
        # It's usually after Categories and before the closing \\ ( https...
        abstract_match = re.search(
            r"Categories:.*?\n\n(.*?)(?=\\\\ \( https|-----)", block, re.DOTALL
        )
        abstract = (
            abstract_match.group(1).strip().replace("\n", " ") if abstract_match else ""
        )

        papers.append(
            {
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors,
                "abstract": abstract,
            }
        )

    return papers
