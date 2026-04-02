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

3.  **Configure API Key using `.env` file (Recommended):**
    You need to obtain an API key from [Finnhub](https://finnhub.io/).
    Create a file named `.env` in the root directory of the project (the same directory where `pyproject.toml` is located) and add your Finnhub API key to it as follows:
    ```dotenv
    FINNHUB_API_KEY=YOUR_API_KEY_HERE
    ```
    **Important:** Replace `'YOUR_API_KEY_HERE'` with your actual Finnhub API key. The server will automatically load this key from the `.env` file when it starts.

    *Alternatively, you can set the `FINNHUB_API_KEY` environment variable in your terminal before running the server:*
    ```bash
    export FINNHUB_API_KEY='YOUR_API_KEY_HERE'
    ```
    *However, using a `.env` file is generally more reliable for ensuring the key is available to the server process.*

4.  **Run the server in Standalone Mode:**
    With dependencies installed and the API key configured (preferably via `.env`), you can start the server independently:
    ```bash
    uv run mcp-finnhub
    ```
    This command launches the MCP server, making it available to clients that can connect to it.

## Usage with MCP Clients (e.g., Gemini CLI)

This MCP server runs independently and exposes financial data through the MCP protocol. To use it with MCP-compatible clients like Gemini CLI, you need to configure the client to point to this running server.

The exact configuration will depend on the client, but generally, you will need to provide:
*   The command to start the server (e.g., `uv run mcp-finnhub`).
*   The directory where the server code resides (if needed by the client).
*   Environment variables, such as `FINNHUB_API_KEY`, if the client manages them.

**Example Configuration (Conceptual, adapt for Gemini CLI):**

Many MCP clients allow you to configure external servers. For instance, if Gemini CLI supports a similar configuration structure to Claude Desktop, you might use something like this:

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
*(Replace `/path/to/mcp-finnhub` with the actual absolute path to your local clone of the repository, and `your_api_key_here` with your actual Finnhub API key. Ensure your `.env` file is correctly set up, or provide the key directly here if the client's configuration mechanism requires it.)*

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
