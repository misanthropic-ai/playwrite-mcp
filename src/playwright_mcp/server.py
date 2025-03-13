import asyncio
import base64
from io import BytesIO
from typing import Dict, List, Optional, Any, Union

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

# Global Playwright state
playwright_instance = None
browser: Optional[Browser] = None
context: Optional[BrowserContext] = None
page: Optional[Page] = None
pages: Dict[str, Page] = {}
current_page_id: Optional[str] = None

server = Server("playwright-mcp")

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available browser screenshot resources.
    """
    resources = []
    
    if pages:
        for page_id, page in pages.items():
            resources.append(
                types.Resource(
                    uri=AnyUrl(f"screenshot://{page_id}"),
                    name=f"Screenshot: {page.url}",
                    description=f"Current screenshot of page at {page.url}",
                    mimeType="image/png",
                )
            )
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> bytes:
    """
    Capture and return a screenshot from the requested page.
    """
    if uri.scheme != "screenshot":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    page_id = uri.host
    if page_id not in pages:
        raise ValueError(f"Page not found: {page_id}")
    
    # Take a screenshot of the page
    screenshot = await pages[page_id].screenshot()
    return screenshot

@server.list_resource_templates()
async def handle_list_resource_templates() -> list[types.ResourceTemplate]:
    """
    List available resource templates for browser automation.
    """
    return []

async def ensure_browser():
    """Ensure the browser is launched and ready."""
    global playwright_instance, browser, context, page, current_page_id
    
    if playwright_instance is None:
        playwright_instance = await async_playwright().start()
        browser = await playwright_instance.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        pages["default"] = page
        current_page_id = "default"

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available Playwright browser automation tools.
    """
    return [
        types.Tool(
            name="navigate",
            description="Navigate to a URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "page_id": {"type": "string"},
                },
                "required": ["url"],
            },
        ),
        types.Tool(
            name="click",
            description="Click on an element by selector",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "page_id": {"type": "string"},
                },
                "required": ["selector"],
            },
        ),
        types.Tool(
            name="type",
            description="Type text into an input element",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "text": {"type": "string"},
                    "page_id": {"type": "string"},
                },
                "required": ["selector", "text"],
            },
        ),
        types.Tool(
            name="get_text",
            description="Get text content from an element",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "page_id": {"type": "string"},
                },
                "required": ["selector"],
            },
        ),
        types.Tool(
            name="get_page_content",
            description="Get the current page HTML content",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="take_screenshot",
            description="Take a screenshot of the current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string"},
                    "selector": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="new_page",
            description="Create a new browser page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string"},
                },
                "required": ["page_id"],
            },
        ),
        types.Tool(
            name="switch_page",
            description="Switch to a different browser page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string"},
                },
                "required": ["page_id"],
            },
        ),
        types.Tool(
            name="get_pages",
            description="List all available browser pages",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="wait_for_selector",
            description="Wait for an element to be visible on the page",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "page_id": {"type": "string"},
                    "timeout": {"type": "number"},
                },
                "required": ["selector"],
            },
        ),
    ]

def get_active_page(page_id: Optional[str] = None) -> Page:
    """Get the active page based on page_id or current default."""
    global current_page_id
    
    if page_id is None:
        page_id = current_page_id
    
    if page_id not in pages:
        raise ValueError(f"Page not found: {page_id}")
    
    return pages[page_id]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests for Playwright browser automation.
    """
    global current_page_id
    
    if not arguments:
        arguments = {}
    
    # Ensure browser is initialized
    await ensure_browser()
    
    # Process tool calls based on name
    if name == "navigate":
        url = arguments.get("url")
        if not url:
            raise ValueError("URL is required")
            
        page = get_active_page(arguments.get("page_id"))
        await page.goto(url)
        return [types.TextContent(type="text", text=f"Navigated to {url}")]
    
    elif name == "click":
        selector = arguments.get("selector")
        if not selector:
            raise ValueError("Selector is required")
            
        page = get_active_page(arguments.get("page_id"))
        await page.click(selector)
        return [types.TextContent(type="text", text=f"Clicked element at selector: {selector}")]
    
    elif name == "type":
        selector = arguments.get("selector")
        text = arguments.get("text")
        if not selector or text is None:
            raise ValueError("Selector and text are required")
            
        page = get_active_page(arguments.get("page_id"))
        await page.fill(selector, text)
        return [types.TextContent(type="text", text=f"Typed '{text}' into {selector}")]
    
    elif name == "get_text":
        selector = arguments.get("selector")
        if not selector:
            raise ValueError("Selector is required")
            
        page = get_active_page(arguments.get("page_id"))
        text = await page.text_content(selector)
        return [types.TextContent(type="text", text=text or "")]
    
    elif name == "get_page_content":
        page = get_active_page(arguments.get("page_id"))
        content = await page.content()
        return [types.TextContent(type="text", text=content)]
    
    elif name == "take_screenshot":
        page = get_active_page(arguments.get("page_id"))
        selector = arguments.get("selector")
        
        if selector:
            screenshot = await page.locator(selector).screenshot()
        else:
            screenshot = await page.screenshot()
        
        # Convert the bytes to base64
        base64_image = base64.b64encode(screenshot).decode('utf-8')
        
        # Return as ImageContent
        return [types.ImageContent(
            type="image",
            image=types.ImageData(
                mime_type="image/png",
                data=base64_image
            )
        )]
    
    elif name == "new_page":
        page_id = arguments.get("page_id")
        if not page_id:
            raise ValueError("Page ID is required")
            
        if page_id in pages:
            raise ValueError(f"Page ID '{page_id}' already exists")
            
        new_page = await context.new_page()
        pages[page_id] = new_page
        current_page_id = page_id
        
        return [types.TextContent(type="text", text=f"Created new page with ID: {page_id}")]
    
    elif name == "switch_page":
        page_id = arguments.get("page_id")
        if not page_id:
            raise ValueError("Page ID is required")
            
        if page_id not in pages:
            raise ValueError(f"Page ID '{page_id}' not found")
            
        current_page_id = page_id
        
        return [types.TextContent(type="text", text=f"Switched to page: {page_id}")]
    
    elif name == "get_pages":
        page_info = []
        for page_id, page in pages.items():
            page_info.append(f"{page_id}: {page.url}")
            
        return [types.TextContent(type="text", text="Available pages:\n" + "\n".join(page_info))]
    
    elif name == "wait_for_selector":
        selector = arguments.get("selector")
        if not selector:
            raise ValueError("Selector is required")
            
        timeout = arguments.get("timeout", 30000)  # Default 30 seconds
        page = get_active_page(arguments.get("page_id"))
        
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return [types.TextContent(type="text", text=f"Element found: {selector}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Timeout waiting for element: {selector}")]
    
    else:
        raise ValueError(f"Unknown tool: {name}")
    
    # Notify clients that resources may have changed
    await server.request_context.session.send_resource_list_changed()

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts for browser automation.
    """
    return [
        types.Prompt(
            name="interpret-page",
            description="Interpret the current web page content and structure",
            arguments=[
                types.PromptArgument(
                    name="page_id",
                    description="ID of the page to interpret",
                    required=False,
                ),
                types.PromptArgument(
                    name="focus",
                    description="What aspect to focus on (full, forms, navigation, text)",
                    required=False,
                )
            ],
        )
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate prompts for interpreting page content.
    """
    global current_page_id
    
    if name != "interpret-page":
        raise ValueError(f"Unknown prompt: {name}")
    
    arguments = arguments or {}
    page_id = arguments.get("page_id", current_page_id)
    focus = arguments.get("focus", "full")
    
    if page_id not in pages:
        raise ValueError(f"Page ID '{page_id}' not found")
    
    page = pages[page_id]
    url = page.url
    
    # Get page title
    title = await page.title()
    
    # Get page content
    content = await page.content()
    
    # Take screenshot for visual context
    screenshot = await page.screenshot()
    screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
    
    # Build the prompt content based on focus
    prompt_text = f"Analyze this web page at URL: {url}\nTitle: {title}\n\n"
    
    if focus == "forms":
        prompt_text += "Focus on identifying all input forms, their fields, and how to interact with them.\n\n"
        # Extract form details
        form_info = await page.evaluate("""() => {
            const forms = Array.from(document.querySelectorAll('form'));
            return forms.map(form => {
                const inputs = Array.from(form.querySelectorAll('input, select, textarea, button'));
                return {
                    id: form.id,
                    action: form.action,
                    method: form.method,
                    inputs: inputs.map(input => ({
                        type: input.tagName.toLowerCase() === 'input' ? input.type : input.tagName.toLowerCase(),
                        name: input.name,
                        id: input.id,
                        placeholder: input.placeholder || '',
                        required: input.required || false
                    }))
                };
            });
        }""")
        prompt_text += f"Form information: {form_info}\n\n"
    
    elif focus == "navigation":
        prompt_text += "Focus on identifying navigation elements, links, and page structure.\n\n"
        # Extract navigation and link details
        nav_info = await page.evaluate("""() => {
            const navs = Array.from(document.querySelectorAll('nav, header, [role="navigation"]'));
            const links = Array.from(document.querySelectorAll('a[href]')).slice(0, 20);
            return {
                navs: navs.map(nav => ({
                    id: nav.id,
                    class: nav.className,
                    links: Array.from(nav.querySelectorAll('a[href]')).map(a => ({
                        text: a.textContent.trim(),
                        href: a.href
                    }))
                })),
                topLinks: links.map(a => ({
                    text: a.textContent.trim(),
                    href: a.href
                }))
            };
        }""")
        prompt_text += f"Navigation information: {nav_info}\n\n"
    
    elif focus == "text":
        prompt_text += "Focus on extracting and summarizing the main text content.\n\n"
        # Extract main text content
        text_content = await page.evaluate("""() => {
            const paragraphs = Array.from(document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, article'));
            return paragraphs.map(p => p.textContent.trim()).filter(t => t.length > 0).join('\\n');
        }""")
        prompt_text += f"Main text content:\n{text_content}\n\n"
    
    else:  # "full"
        prompt_text += "Provide a complete analysis of the page elements, content, and functionality.\n\n"
        prompt_text += "Key elements to identify:\n- Main content\n- Navigation\n- Forms\n- Interactive elements\n- Key information\n\n"
    
    return types.GetPromptResult(
        description=f"Interpret web page at {url}",
        messages=[
            types.PromptMessage(
                role="user",
                content=[
                    types.TextContent(type="text", text=prompt_text),
                    types.ImageContent(
                        type="image",
                        image=types.ImageData(
                            mime_type="image/png",
                            data=screenshot_base64
                        )
                    )
                ]
            )
        ],
    )

async def cleanup():
    """Clean up Playwright resources."""
    global browser, playwright_instance
    
    if browser:
        await browser.close()
    
    if playwright_instance:
        await playwright_instance.stop()

async def main():
    """Main entry point for the server."""
    try:
        # Run the server using stdin/stdout streams
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="playwright-mcp",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        # Ensure we clean up resources when the server shuts down
        await cleanup()