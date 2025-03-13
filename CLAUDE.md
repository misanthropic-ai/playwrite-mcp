# CLAUDE.md - Development Guidelines

## Core Commands
- Install dependencies: `uv add playwright && playwright install chromium`
- Run server: `playwright-mcp`
- Debug with inspector: `npx @modelcontextprotocol/inspector uv --directory $(pwd) run playwright-mcp`
- Build package: `uv build`
- Publish: `uv publish --token $UV_PUBLISH_TOKEN`

## Code Style Guidelines
- Use Python 3.11+
- Imports: stdlib first, then third-party, then local (grouped with blank lines)
- Type annotations required for all function signatures
- Use clear docstrings for all public functions and classes
- Error handling: use descriptive ValueError exceptions with specific messages
- Naming: snake_case for functions/variables, PascalCase for classes
- Async/await patterns preferred for all I/O operations
- Keep state management clearly defined (global browser state variables)
- Function parameters should use Optional types when appropriate

## Project Structure
- Entry point at `playwright_mcp/__init__.py:main`
- Core server implementation in `server.py`
- MCP protocol handling via `mcp` package
- Playwright browser automation via `playwright.async_api`

## Browser Automation Tools
- Navigation: navigate, new_page, switch_page, get_pages
- Interaction: click, type, wait_for_selector
- Content: get_text, get_page_content, take_screenshot
- Page ID management: All pages have a unique ID for reference