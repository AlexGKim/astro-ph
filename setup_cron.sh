#!/bin/bash
CRON_JOB="0 2 * * * cd /Users/akim/Projects/astro-ph && PYTHONPATH=src /Users/akim/miniforge3/bin/python src/main.py --email agkim@lbl.gov >> /Users/akim/Projects/astro-ph/astro-ph-cron.log 2>&1"
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
