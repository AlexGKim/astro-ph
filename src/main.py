import os
import argparse
from dotenv import load_dotenv
from email_client import get_gmail_service, fetch_latest_astroph_email, send_email
from arxiv_parser import parse_email_text
from llm_filter import filter_papers
from pdf_processor import download_and_extract_text
from summarizer import summarize_paper

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

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set in environment.")
        return

    print("Authenticating with Gmail...")
    service = get_gmail_service()

    print("Fetching latest astro-ph email...")
    mark_read = not args.no_mark_read
    email_text = fetch_latest_astroph_email(service, mark_read=mark_read)

    if not email_text:
        print("No unread astro-ph emails found.")
        return

    print("Parsing email...")
    papers = parse_email_text(email_text)
    print(f"Found {len(papers)} papers in email.")

    if not papers:
        return

    print("Filtering papers with LLM...")
    matched_ids = filter_papers(papers, api_key=api_key)
    print(f"Found {len(matched_ids)} matching papers: {matched_ids}")

    if not matched_ids:
        print("No papers matched interests today.")
        return

    # Create a lookup dict for matched papers
    matched_papers = [p for p in papers if p["arxiv_id"] in matched_ids]

    summaries = []
    for paper in matched_papers:
        print(f"Processing PDF for {paper['arxiv_id']}...")
        full_text = download_and_extract_text(paper["arxiv_id"])

        if not full_text:
            print(f"Warning: Could not extract text for {paper['arxiv_id']}")
            continue

        print(f"Summarizing {paper['arxiv_id']}...")
        summary = summarize_paper(paper, full_text, api_key=api_key)
        summaries.append(summary)

    if not summaries:
        print("No summaries generated.")
        return

    final_report = "# Astro-ph Daily Summary\n\n" + "\n\n---\n\n".join(summaries)

    if args.dry_run:
        print("\n--- DRY RUN OUTPUT ---\n")
        print(final_report)
    else:
        print(f"Sending email to {args.email}...")
        send_email(service, args.email, "Your Astro-ph Daily Summary", final_report)
        print("Done!")


if __name__ == "__main__":
    main()
