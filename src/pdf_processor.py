import arxiv
import fitz  # PyMuPDF
import os


def download_and_extract_text(arxiv_id):
    """Downloads PDF from arXiv and extracts text."""
    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    paper = next(iter(client.results(search)), None)

    if not paper:
        print(f"Paper {arxiv_id} not found via arXiv API.")
        return ""

    filename = f"{arxiv_id.replace('.', '_')}.pdf"

    try:
        # Download
        downloaded = paper.download_pdf(filename=filename)
        if downloaded:
            filename = downloaded

        # Extract Text
        text = ""
        with fitz.open(filename) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        print(f"Error processing {arxiv_id}: {e}")
        return ""
    finally:
        # Cleanup
        try:
            os.remove(filename)
        except OSError:
            pass
