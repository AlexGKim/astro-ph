# Astro-ph Daily Summarizer

An automated Python script that reads your daily arXiv `astro-ph` digest email, uses LLMs to filter papers matching your specific research interests, downloads and extracts the full text from the relevant PDFs, summarizes them, and sends you a clean Markdown report.

## Features
- **Automated Ingestion**: Authenticates with Gmail to find your latest unread `astro-ph` daily email.
- **Smart Filtering**: Uses OpenAI's `gpt-4o-mini` to filter the email's papers against your custom research interests.
- **Full-Text Context**: Automatically downloads the PDF of matching papers and extracts the text using PyMuPDF.
- **Expert Summarization**: Uses OpenAI's `gpt-4o` to provide a structured summary (Gist, Methodology, Findings, Limitations) based on the *full text* of the paper.
- **Delivery**: Emails the final Markdown report directly to you.

## Prerequisites
- Python 3.10+
- [OpenAI API Key](https://platform.openai.com/api-keys)
- [Google Cloud Console Project](https://console.cloud.google.com/) with the Gmail API enabled.

## Setup & Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Create a `.env` file in the root of the project and add your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
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
python src/main.py --email your.email@example.com
```

### First Run (Authentication)
The very first time you run the script, it will open a browser window asking you to authorize the app with your Google account. Once authorized, it will generate a `token.json` file. Subsequent runs (e.g., via `cron`) will use this token silently.

### Command Line Options
- `--email` (required): The destination email address to send the final summary report.
- `--dry-run` (optional): Process everything and print the final report to the console, but **do not** send the final email.
- `--no-mark-read` (optional): Do not mark the original `astro-ph` email as read in your Gmail inbox.

Example for testing:
```bash
python src/main.py --email your.email@example.com --dry-run --no-mark-read
```

## Testing

To run the unit tests, ensure you are in the project root and run:
```bash
pytest
```
