# Gemini CLI & MCP Finnhub Integration

This project is a high-performance MCP server for the Finnhub API, optimized for use with Gemini CLI and Claude Desktop.

## Quick Reference: Tool Selection

For the best results, use the appropriate server based on the market you are analyzing:

| Market | Recommended Server | Why? |
| :--- | :--- | :--- |
| **US Stocks** (AAPL, TSLA, etc.) | `mcp-finnhub` | High-quality, real-time financial data for US markets. |
| **Swedish/EU Stocks** (NEWA-B.ST, etc.) | `stock-analysis` | Finnhub Free Tier restricts international data (403 Access Denied). |

## Caching & Performance

To optimize API usage and improve responsiveness, `mcp-finnhub` includes a lightweight TTL (Time-To-Live) caching layer:
*   **Quotes:** 1-minute TTL.
*   **Technical/Candles:** 5-minute TTL.
*   **News:** 10-minute TTL.
*   **Profiles/Financials/Insiders:** 1-hour TTL.

## Resolution Validation

Tools requiring a `resolution` parameter (like candles and technical indicators) only support the following values:
*   `1`, `5`, `15`, `30`, `60` (Minutes)
*   `D` (Day), `W` (Week), `M` (Month)

## Common Error: "Access Denied (403)"

If you encounter a **403 Access Denied** error when using `mcp-finnhub`, it is almost always due to Finnhub's API Tier restrictions:
*   **Free Tier:** Restricted to US-listed equities and specific endpoints.
*   **International Markets:** Accessing symbols like `.ST` (Stockholm) or `.DE` (Frankfurt) typically requires a **paid Finnhub plan**.

## Environment & Authentication

The `mcp-finnhub` server uses a **System-First** loading logic:
1.  It checks the **system environment** (e.g., your `.bashrc` export) first.
2.  It falls back to the **`.env` file** in the project root only if the system environment is empty.
3.  It proactively blocks placeholder keys to prevent silent failures.

### Diagnostic Command
To verify your setup and API access at any time, run:
```bash
uv run scripts/setup_check.py
```
