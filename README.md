# Astro-ph Daily Summarizer

An automated Python script that queries the arXiv API for the latest `astro-ph` papers, uses Amazon Bedrock LLMs to filter papers matching your specific research interests, downloads and extracts the full text from the relevant PDFs, summarizes them, and sends you a clean Markdown report via email.

## Features
- **Automated Ingestion**: Fetches the last 24 hours of astrophysics papers (`cat:astro-ph*`) directly from the arXiv API.
- **Smart Filtering**: Uses Amazon Bedrock (Claude Haiku) to filter the incoming papers against your custom research interests.
- **Full-Text Context**: Automatically downloads the PDF of matching papers and extracts the text using PyMuPDF.
- **Expert Summarization**: Uses Amazon Bedrock (Claude Sonnet) to provide a structured summary (The Gist, Key Methodology, Main Findings, Limitations) based on the *full text* of the paper.
- **Delivery**: Authenticates with Gmail to email the final Markdown report directly to you.

## Prerequisites
- Python 3.10+
- [AWS Account](https://aws.amazon.com/) with Bedrock access (specifically Anthropic Claude models enabled).
- [Google Cloud Console Project](https://console.cloud.google.com/) with the Gmail API enabled (for sending emails).

## Setup & Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS Credentials**:
   Create a `.env` file in the root of the project and add your AWS credentials. Ensure your AWS user has permissions to invoke Bedrock models:
   ```env
   AWS_ACCESS_KEY_ID="your_aws_access_key_here"
   AWS_SECRET_ACCESS_KEY="your_aws_secret_key_here"
   ```

3. **Set up Gmail API Credentials**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Enable the **Gmail API** for your project.
   - Go to **Credentials** > **Create Credentials** > **OAuth client ID**.
   - Choose **Desktop app** as the application type.
   - Download the resulting JSON file and save it in the root of this project as `credentials.json`.

## Customizing Your Interests

Currently, your research interests are configured in `src/llm_filter.py`. Open that file and edit the `INTERESTS` string to match your domain (e.g., specific cosmology probes, instrumentations, or phenomena).

## Usage

Run the orchestrator script:

```bash
PYTHONPATH=src python src/main.py --email your.email@example.com
```

### First Run (Authentication)
The very first time you run the script without `--dry-run`, it will open a browser window asking you to authorize the app with your Google account. Once authorized, it will generate a `token.json` file. Subsequent runs (e.g., via `cron`) will use this token silently to send the emails.

### Command Line Options
- `--email` (required): The destination email address to send the final summary report.
- `--dry-run` (optional): Process everything and print the final report to the console, but **do not** send the final email.
- `--debug` (optional): Run in debug mode. Expands the arXiv search window to 7 days instead of 24 hours, and removes the max results limit to process larger batches.

Example for testing without sending an email:
```bash
PYTHONPATH=src python src/main.py --email your.email@example.com --dry-run
```

## Testing

To run the unit tests, ensure you are in the project root and run:
```bash
PYTHONPATH=src pytest -v
```
