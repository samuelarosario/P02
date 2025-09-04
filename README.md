# P02 - API Data Puller

A Python project for pulling data from API endpoints with robust error handling, rate limiting, and multiple output formats.

## Features

- **HTTP API Client**: Built on `requests` with retry logic and rate limiting
- **Multiple Output Formats**: JSON, CSV, and Excel support
- **Environment Configuration**: Secure API key management with `.env` files
- **Comprehensive Logging**: Detailed logging with `loguru`
- **Async Support**: Optional async HTTP client with `httpx` and `aiohttp`
- **Data Processing**: Built-in pandas integration for data manipulation

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

3. **Run Examples**:
   ```bash
   cd src
   python examples.py
   ```

## Project Structure

```
src/
├── api_data_puller.py  # Main API client class
├── config.py           # Configuration management
└── examples.py         # Usage examples
```

## Agent Instructions

**Important Guidelines for AI Agent Interactions:**

1. **Execution Verification**: All script executions and commands must be verified and approved by me before running.

2. **Temporary Scripts Management**: 
   - Use a `temp scripts` folder for all temporary scripts and files
   - Delete the `temp scripts` folder and its contents after successful execution runs
   - Do not leave temporary files in the project directory

3. **Session Guidelines**: These instructions should be loaded and followed each time I connect or start a new session with the agent.
