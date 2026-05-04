import logging
from openai import OpenAI, OpenAIError


def summarize_paper(paper_metadata, full_text, api_key=None):
    """Sends full text to LLM for a structured summary."""
    client = OpenAI(api_key=api_key)

    # Truncate text if it's absurdly long, though gpt-4o handles 128k
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
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
    except OpenAIError as e:
        logging.error(f"OpenAI API error during summarization: {e}")
        return f"## [{paper_metadata['title']}](https://arxiv.org/abs/{paper_metadata['arxiv_id']})\n\n**Error:** Could not generate summary due to API error."
    except Exception as e:
        logging.error(f"Unexpected error during summarization: {e}")
        return f"## [{paper_metadata['title']}](https://arxiv.org/abs/{paper_metadata['arxiv_id']})\n\n**Error:** Could not generate summary due to an unexpected error."
