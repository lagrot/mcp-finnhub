# MCP Finnhub Server

An MCP (Model Context Protocol) server for the [Finnhub API](https://finnhub.io/), providing financial analysis tools for Claude, Gemini, and other MCP-compatible clients.

## Features

- **Company Profile**: Get basic company info (name, ticker, industry, market cap).
- **Financial Metrics**: Get key financial ratios (P/E, margins, growth).
- **Stock Candles**: Get historical price data (OHLCV).
- **Market News**: Get company-specific and general market news.
- **Technical Indicators**: Get aggregate Buy/Sell/Hold signals.
- **Insider Transactions**: Get recent insider trades.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) installed.
- A Finnhub API Key. Get one for free at [finnhub.io](https://finnhub.io/dashboard).

## Setup

1. Clone this repository.
2. Create a `.env` file (optional, see below) or set the environment variable.

### Environment Variable

The server requires the `FINNHUB_API_KEY` environment variable.

```bash
export FINNHUB_API_KEY=your_api_key_here
```

## Usage

### Running Locally

You can run the server directly using `uv`:

```bash
uv run mcp-finnhub
```

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
