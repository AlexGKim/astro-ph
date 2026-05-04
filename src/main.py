import argparse
import logging
from dotenv import load_dotenv
from email_client import get_gmail_service, fetch_latest_astroph_email, send_email
from arxiv_parser import parse_email_text
from llm_filter import filter_papers
from pdf_processor import download_and_extract_text
from summarizer import summarize_paper

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Astro-ph Daily Summarizer")
    parser.add_argument(
        "--dry-run", action="store_true", help="Process but don't send final email"
    )
    parser.add_argument(
        "--no-mark-read", action="store_true", help="Don't mark the arxiv email as read"
    )
    parser.add_argument(
        "--email", type=str, required=True, help="Email address to send results to"
    )
    args = parser.parse_args()

    logging.info("Authenticating with Gmail...")
    try:
        service = get_gmail_service()
    except Exception as e:
        logging.error(f"Gmail authentication failed: {e}")
        return

    logging.info("Fetching latest astro-ph email...")
    mark_read = not args.no_mark_read
    email_text = fetch_latest_astroph_email(service, mark_read=mark_read)

    if not email_text:
        logging.info("No unread astro-ph emails found.")
        return

    logging.info("Parsing email...")
    papers = parse_email_text(email_text)

    if not papers:
        logging.info("No valid papers found to parse.")
        return

    logging.info(f"Found {len(papers)} papers in email.")

    logging.info("Filtering papers with LLM...")
    matched_ids = filter_papers(papers)
    logging.info(f"Found {len(matched_ids)} matching papers: {matched_ids}")

    if not matched_ids:
        logging.info("No papers matched interests today.")
        return

    # Create a lookup dict for matched papers
    matched_papers = [p for p in papers if p["arxiv_id"] in matched_ids]

    summaries = []
    for paper in matched_papers:
        logging.info(f"Processing PDF for {paper['arxiv_id']}...")
        full_text = download_and_extract_text(paper["arxiv_id"])

        if not full_text:
            logging.warning(f"Could not extract text for {paper['arxiv_id']}")
            continue

        logging.info(f"Summarizing {paper['arxiv_id']}...")
        summary = summarize_paper(paper, full_text)
        summaries.append(summary)

    if not summaries:
        logging.info("No summaries generated.")
        return

    final_report = "# Astro-ph Daily Summary\n\n" + "\n\n---\n\n".join(summaries)

    if args.dry_run:
        logging.info("\n--- DRY RUN OUTPUT ---\n")
        print(final_report)
    else:
        logging.info(f"Sending email to {args.email}...")
        result = send_email(
            service, args.email, "Your Astro-ph Daily Summary", final_report
        )
        if result:
            logging.info("Email sent successfully!")
        else:
            logging.error("Failed to send email.")


if __name__ == "__main__":
    main()
