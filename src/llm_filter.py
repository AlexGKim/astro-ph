import json
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError

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


def filter_papers(papers, model="anthropic.claude-3-haiku-20240307-v1:0"):
    """Uses LLM to filter papers. Returns list of matched arXiv IDs."""
    if not papers:
        return []

    client = boto3.client("bedrock-runtime")
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
            response = client.converse(
                modelId=model,
                messages=[
                    {"role": "user", "content": [{"text": prompt}]},
                ],
                system=[{"text": "You output JSON arrays of strings."}],
                inferenceConfig={"temperature": 0.0},
            )

            content = response["output"]["message"]["content"][0]["text"].strip()

            # Handle markdown code blocks if the LLM adds them
            if content.startswith("```"):
                content = content.strip("`").removeprefix("json").strip()

            matched_ids = json.loads(content)
            all_matched_ids.extend(matched_ids)

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Bedrock API error: {e}")
            continue
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON: {content}")
            continue

    return all_matched_ids
