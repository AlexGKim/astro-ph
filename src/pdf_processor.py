import arxiv
import fitz  # PyMuPDF
import os
import tempfile
import logging


def download_and_extract_text(arxiv_id):
    """Downloads PDF from arXiv and extracts text."""
    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    paper = next(client.results(search), None)

    if not paper:
        logging.warning(f"Paper {arxiv_id} not found via arXiv API.")
        return ""

    fd, filename = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    try:
        # Download
        paper.download_pdf(filename=filename)

        # Extract Text
        text = ""
        with fitz.open(filename) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        logging.error(f"Error processing {arxiv_id}: {e}")
        return ""
    finally:
        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)
