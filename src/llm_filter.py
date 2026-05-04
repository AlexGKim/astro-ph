# src/llm_filter.py
import json
import logging
import openai
from openai import OpenAI

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


def filter_papers(papers, api_key=None, model="gpt-4o-mini"):
    """Uses LLM to filter papers. Returns list of matched arXiv IDs."""
    if not papers:
        return []

    client = OpenAI(api_key=api_key)
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
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You output JSON arrays of strings."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )

            if response.choices[0].message.content is None:
                continue

            content = response.choices[0].message.content.strip()

            # Handle markdown code blocks if the LLM adds them
            if content.startswith("```"):
                content = content.strip("`").removeprefix("json").strip()

            matched_ids = json.loads(content)
            all_matched_ids.extend(matched_ids)

        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            continue
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON: {content}")
            continue

    return all_matched_ids
