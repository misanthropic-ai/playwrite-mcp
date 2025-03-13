# playwright-mcp

Playwright wrapper for MCP (Model Context Protocol). This server enables LLM-powered clients to control a browser for automation tasks.

## Components

### Resources

The server exposes resources for accessing browser screenshots:
- Screenshot resource URI: `screenshot://{page_id}`
- Screenshot resources are automatically available for all open pages

### Prompts

The server provides a prompt to help clients interpret web pages:
- `interpret-page`: Analyzes the current web page content and structure
  - Optional `page_id` argument to select which page to interpret
  - Optional `focus` argument to focus on specific aspects (full, forms, navigation, text)
  - Returns both text analysis and a screenshot of the page

### Tools

The server implements a comprehensive set of browser automation tools:

- **Browser navigation**
  - `navigate`: Go to a specific URL
  - `new_page`: Create a new browser page with a specific ID
  - `switch_page`: Switch to a different browser page
  - `get_pages`: List all available browser pages

- **Page interaction**
  - `click`: Click on an element using CSS selector
  - `type`: Type text into an input element
  - `wait_for_selector`: Wait for an element to appear on the page

- **Content extraction**
  - `get_text`: Get text content from an element
  - `get_page_content`: Get the entire page HTML
  - `take_screenshot`: Capture visual state of the page or element

## Configuration

### Install Dependencies

```bash
uv add playwright
playwright install chromium
```

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`  
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  
  ```json
  "mcpServers": {
    "playwright-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/shannon/Workspace/artivus/playwright-mcp",
        "run",
        "playwright-mcp"
      ]
    }
  }
  ```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  
  ```json
  "mcpServers": {
    "playwright-mcp": {
      "command": "uvx",
      "args": [
        "playwright-mcp"
      ]
    }
  }
  ```
</details>

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /Users/shannon/Workspace/artivus/playwright-mcp run playwright-mcp
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.