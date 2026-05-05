import arxiv
import fitz  # PyMuPDF
import os
import tempfile
import logging
import time


def download_and_extract_text(arxiv_id, max_retries=3):
    """Downloads PDF from arXiv and extracts text with retries."""

    # Custom client with longer delay and more retries
    client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=5)
    search = arxiv.Search(id_list=[arxiv_id])

    for attempt in range(max_retries):
        try:
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
            finally:
                # Cleanup
                if os.path.exists(filename):
                    os.remove(filename)

        except arxiv.HTTPError as e:
            if e.status in (429, 503):
                wait_time = (attempt + 1) * 10
                logging.warning(
                    f"Rate limited (HTTP {e.status}) for {arxiv_id}. Waiting {wait_time}s... (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait_time)
            else:
                logging.error(f"HTTP Error processing {arxiv_id}: {e}")
                return ""
        except Exception as e:
            logging.error(f"Error processing {arxiv_id}: {e}")
            return ""

    logging.error(f"Failed to download {arxiv_id} after {max_retries} retries.")
    return ""
