# Web Tests Analysis Tools

This directory contains a suite of tools for parsing, analyzing, and visualizing performance metrics for web tests.

## 1. Web App (UI)

The web app provides a visual dashboard for comparing metrics across multiple dataset groups (using local paths or `gs://` URIs). It automatically performs statistical analysis (such as permutation tests and Holm-Bonferroni FWER corrections) to highlight regressions and improvements.

### Usage

The web app is hosted at:
[https://chromium-workloads.web.app/web-tests/main/analysis/web/index.html](https://chromium-workloads.web.app/web-tests/main/analysis/web/index.html)

Simply navigate to the URL above to start using the dashboard.

#### Features
- **N-Group Comparison**: Add as many dataset groups as you want and compare their metrics side-by-side.
- **Plotly Visualizations**: Click on any metric row to view interactive Violin and Box plots comparing raw data points across all groups.
- **URL Syncing**: The dashboard state (selected test, highlighted metric, active graphs, and filters) is automatically synced with the URL. You can easily share links to specific data views with others.

### Development

If you are developing the web app locally, you must start a local HTTP server in the root `web-tests` directory. The server must run on port `8081` to comply with Google OAuth Client ID restrictions (required for `gs://` dataset loading).

1. Navigate to the `web-tests` root directory:
   ```bash
   cd /path/to/web-tests
   ```
2. Start the HTTP server:
   ```bash
   python3 -m http.server 8081
   ```
3. Open the app in your local browser: [http://localhost:8081/analysis/web/index.html](http://localhost:8081/analysis/web/index.html)

---

## 2. MCP Server (Model Context Protocol)

The MCP server exposes the core analytical functions of this project as a suite of tools. This allows AI agents to autonomously ingest datasets, run statistical tests, and formulate automated performance reports.

### Setup

To enable the `web-tests-analyzer` MCP server, you need to configure your agent's MCP settings. Add the following to your `~/.gemini/mcp_config.json`:

```json
{
  "mcpServers": {
    "web-tests-analyzer": {
      "command": "/path/to/web-tests/third_party/crossbench/third_party/node/linux/node-linux-x64/bin/node",
      "args": [
        "--max-old-space-size=8192",
        "/path/to/web-tests/web-tests/analysis/mcp/mcp.js"
      ]
    }
  }
}
```

*Note: The `--max-old-space-size=8192` flag ensures the Node.js process has enough memory to parse large JSON datasets.*

### Available Tools

Once configured, the agent has access to the following tools:

- `get_dataset_metadata`: Get system and environment metadata for the given dataset groups (e.g. OS, RAM, versions).
- `compare_datasets`: Load dataset JSON files and find which tests ran in each group, and detect any mismatching tests.
- `analyze_test`: Statistically compare metrics for a specific test across dataset groups.
- `get_important_metrics`: Retrieve the list of "top of mind" metrics for a specific test.
- `analyze_all_tests`: Analyze the metrics for all common tests across the dataset groups.
- `get_significant_changes`: Automatically analyze all common tests and filter the results to only show metrics with a statistically significant change.

### Example Agent Prompts

Example prompts are located in the `prompt_examples/` directory. You can use these text files to directly prompt your AI assistant to perform analyses.
