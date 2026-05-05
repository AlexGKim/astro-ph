import argparse
import logging
from dotenv import load_dotenv
from email_client import get_gmail_service, send_email
from arxiv_fetcher import fetch_daily_astroph_papers
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
        "--email", type=str, required=True, help="Email address to send results to"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode (7 days window, no max results)",
    )
    args = parser.parse_args()

    # If we are actually sending an email, authenticate early to fail fast
    service = None
    if not args.dry_run:
        logging.info("Authenticating with Gmail for delivery...")
        try:
            service = get_gmail_service()
        except Exception as e:
            logging.error(f"Gmail authentication failed: {e}")
            return

    logging.info("Fetching latest astro-ph papers from arXiv API...")
    papers = fetch_daily_astroph_papers(debug=args.debug)

    if not papers:
        logging.info("No recent astro-ph papers found.")
        return

    time_window = "7 days" if args.debug else "24 hours"
    logging.info(f"Found {len(papers)} papers from the last {time_window}.")

    logging.info("Filtering papers with LLM...")
    matched_ids = filter_papers(papers)
    logging.info(f"Found {len(matched_ids)} matching papers: {matched_ids}")

    if not matched_ids:
        logging.info("No papers matched interests today.")
        return

    # Create a list of matched papers
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
