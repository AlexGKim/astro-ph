# Bedrock Transition Design

## Overview
Transition from OpenAI to Amazon Bedrock for LLM capabilities.

## Models
- Filtering: Claude 3 Haiku (`anthropic.claude-3-haiku-20240307-v1:0`)
- Summarization: Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20240620-v1:0`)

## Changes
1. Replace `openai` with `boto3` in requirements.
2. Update `llm_filter.py` and `summarizer.py` to use `boto3.client('bedrock-runtime')`.
3. Rely on standard AWS credentials in the environment rather than a specific API key.
4. Update unit tests to mock `boto3`.
