# MCP Finnhub Server

An MCP (Model Context Protocol) server for the [Finnhub API](https://finnhub.io/), providing financial analysis tools for Claude, Gemini, and other MCP-compatible clients.

## Features

- **Company Profile**: Get basic company info (name, ticker, industry, market cap).
- **Financial Metrics**: Get key financial ratios (P/E, margins, growth).
- **Stock Candles**: Get historical price data (OHLCV).
- **Market News**: Get company-specific and general market news.
- **Technical Indicators**: Get aggregate Buy/Sell/Hold signals.
- **Insider Transactions**: Get recent insider trades.

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd mcp-finnhub
    ```
    *(Replace `<repository_url>` with the actual repository URL.)*

2.  **Install dependencies using uv:**
    This project uses `uv` for dependency management.
    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt # Or if no requirements.txt, use 'uv pip install .'
    ```
    *Note: If `requirements.txt` is not present, you might need to adjust the installation command based on your project's structure (e.g., `uv pip install .` or by inspecting `pyproject.toml`).*

3.  **Set up environment variables:**
    You need to obtain an API key from [Finnhub](https://finnhub.io/).
    Once you have your API key, set the `FINNHUB_API_KEY` environment variable for your current terminal session:
    ```bash
    export FINNHUB_API_KEY='YOUR_API_KEY_HERE'
    ```
    **Important:** Replace `'YOUR_API_KEY_HERE'` with your actual Finnhub API key. This command ensures the key is available when running the server.

4.  **Run the server:**
    With dependencies installed and the API key set, you can start the server:
    ```bash
    uv run mcp-finnhub
    ```

## Usage

### Running Locally

Follow the steps in the "Setup Instructions" section above.

### Configuration for Claude Desktop

Add the following to your Claude Desktop configuration file (e.g., `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%/Claude/claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "finnhub": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-finnhub",
        "run",
        "mcp-finnhub"
      ],
      "env": {
        "FINNHUB_API_KEY": "your_api_key_here"
      }
    }
  }
}
```
*(Ensure `/path/to/mcp-finnhub` is the correct absolute path to your local clone of the repository, and replace `your_api_key_here` with your actual Finnhub API key.)*

## Development

### Linting and Formatting

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

```bash
uv run ruff check . --fix
uv run ruff format .
```

### Testing

```bash
uv run pytest
```

## License

MIT
