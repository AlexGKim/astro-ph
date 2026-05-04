# src/llm_filter.py
from openai import OpenAI
import json

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


def filter_papers(papers, api_key=None):
    """Uses LLM to filter papers. Returns list of matched arXiv IDs."""
    if not papers:
        return []

    client = OpenAI(api_key=api_key)

    prompt = f"""
    You are an expert astrophysicist evaluating papers for a researcher.
    The researcher's interests are:
    {INTERESTS}
    
    Here is a list of papers from today's astro-ph:
    """

    for p in papers:
        prompt += (
            f"\nID: {p['arxiv_id']}\nTitle: {p['title']}\nAbstract: {p['abstract']}\n"
        )

    prompt += """
    Based on the titles and abstracts, identify which papers align closely with the researcher's interests.
    Return ONLY a JSON array of the matching ID strings.
    Example: ["2405.00001", "2405.00003"]
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You output JSON arrays of strings."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )

    content = response.choices[0].message.content.strip()
    # Handle markdown code blocks if the LLM adds them
    if content.startswith("```json"):
        content = content[7:-3]
    elif content.startswith("```"):
        content = content[3:-3]

    try:
        matched_ids = json.loads(content)
        return matched_ids
    except json.JSONDecodeError:
        print(f"Error decoding JSON: {content}")
        return []
