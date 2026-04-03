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

4.  **Validate your API key (Recommended):**
    Before running the server, you can verify that your API key is valid and the environment is correctly set up:
    ```bash
    uv run scripts/validate_api.py
    ```

5.  **Run the server in Standalone Mode:**
    With dependencies installed and the API key configured (preferably via `.env`), you can start the server independently:
    ```bash
    uv run mcp-finnhub
    ```
    This command launches the MCP server, making it available to clients that can connect to it.

## Usage with MCP Clients (e.g., Gemini CLI)

This MCP server runs independently and exposes financial data through the MCP protocol. To use it with MCP-compatible clients like Gemini CLI, you need to configure the client to point to this running server.

**Adding the MCP Server to Gemini CLI:**

You can register the `mcp-finnhub` server with Gemini CLI using the following command:

```bash
gemini mcp add stock-analysis uv --project <PROJECT_PATH> 'uv run mcp-finnhub'
```

**Adding the MCP Server to Claude Desktop:**

To use this server with Claude Desktop, add it to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-finnhub": {
      "command": "uv",
      "args": [
        "--project",
        "<PROJECT_PATH>",
        "run",
        "mcp-finnhub"
      ],
      "env": {
        "FINNHUB_API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

**Explanation of the Configuration:**

*   **`gemini mcp add stock-analysis`**: This command registers a new MCP server configuration within Gemini CLI, naming it `stock-analysis`.
*   **`uv`**: Specifies that `uv` is the runner used to execute the server command.
*   **`--project <PROJECT_PATH>`**: This argument points Gemini CLI to your project's root directory. **Replace `<PROJECT_PATH>` with the actual absolute path to your local clone of the repository.**
*   **`'uv run mcp-finnhub'`**: This is the command that Gemini CLI will execute to start and manage the MCP server.

**General Integration Notes:**

*   **API Key Management**: While the command above includes the API key directly, it is highly recommended to manage your Finnhub API key using a `.env` file in your project's root directory (`<PROJECT_PATH>/.env`). The server script uses `load_dotenv()` to pick up the key from this file. Gemini CLI's configuration might also support loading environment variables from a `.env` file, or you might need to pass the key explicitly as shown in the command.
*   **Project Path**: Ensure `<PROJECT_PATH>` is the correct absolute path to your project.

## Troubleshooting & API Tiers

If you encounter a **403 Forbidden** error when using certain tools (e.g., `get_technical_indicators`), it is likely because that specific endpoint is restricted to Finnhub's **paid tiers**.

- **Free Tier:** Generally includes Company Profile, Basic Financials, and some News.
- **Paid Tier:** Often required for Technical Indicators, Stock Candles (historical), and real-time data beyond a certain threshold.

To verify your key's access, run the validation script:
```bash
uv run scripts/validate_api.py
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
