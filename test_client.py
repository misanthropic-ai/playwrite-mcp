import asyncio
import os
import sys
import json
from typing import Optional, Dict, Any, List
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# This client doesn't use Claude directly, but instead manually tests our tools

class PlaywrightTestClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.tools = []
        self.prompts = []
        self.resources = []
    
    async def connect_to_server(self):
        """Connect to our Playwright MCP server directly"""
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "playwright-mcp"],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        self.tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in self.tools])
        
        # List available prompts
        response = await self.session.list_prompts()
        self.prompts = response.prompts
        print("Available prompts:", [prompt.name for prompt in self.prompts])
        
        # List available resources
        response = await self.session.list_resources()
        self.resources = response.resources
        print("Initial resources:", [f"{r.name} ({r.uri})" for r in self.resources])
    
    async def run_test_sequence(self):
        """Run a sequence of tests to verify server functionality"""
        try:
            # Test 1: Navigate to a webpage
            print("\n📝 TEST: Navigate to a webpage")
            response = await self.session.call_tool(
                "navigate", 
                {"url": "https://example.com"}
            )
            print(f"Response: {response.content[0].text}")
            
            # Wait a moment for page to load
            await asyncio.sleep(2)
            
            # Test 2: Take a screenshot
            print("\n📝 TEST: Take a screenshot")
            response = await self.session.call_tool(
                "take_screenshot", 
                {}
            )
            if response.content[0].type == "image":
                print("✅ Received screenshot image")
            else:
                print(f"❌ Failed to get screenshot: {response.content}")
            
            # Test 3: Get page content
            print("\n📝 TEST: Get page content")
            response = await self.session.call_tool(
                "get_page_content", 
                {}
            )
            content = response.content[0].text
            print(f"Content length: {len(content)} characters")
            print(f"Preview: {content[:200]}...")
            
            # Test 4: Get text from an element
            print("\n📝 TEST: Get text from h1 element")
            response = await self.session.call_tool(
                "get_text", 
                {"selector": "h1"}
            )
            print(f"H1 text: {response.content[0].text}")
            
            # Test 5: Create a new page
            print("\n📝 TEST: Create a new page")
            response = await self.session.call_tool(
                "new_page", 
                {"page_id": "test-page"}
            )
            print(f"Response: {response.content[0].text}")
            
            # Check resources after new page
            response = await self.session.list_resources()
            print("Resources after new page:", [f"{r.name} ({r.uri})" for r in response.resources])
            
            # Test 6: Navigate in new page
            print("\n📝 TEST: Navigate in the new page")
            response = await self.session.call_tool(
                "navigate", 
                {"url": "https://playwright.dev", "page_id": "test-page"}
            )
            print(f"Response: {response.content[0].text}")
            
            # Wait a moment for page to load
            await asyncio.sleep(2)
            
            # Test 7: Switch pages
            print("\n📝 TEST: Switch between pages")
            response = await self.session.call_tool(
                "switch_page", 
                {"page_id": "test-page"}
            )
            print(f"Response: {response.content[0].text}")
            
            # Test 8: List all pages
            print("\n📝 TEST: List all pages")
            response = await self.session.call_tool(
                "get_pages", 
                {}
            )
            print(f"Pages: {response.content[0].text}")
            
            # Test 9: Test the interpret-page prompt
            print("\n📝 TEST: Test interpret-page prompt")
            response = await self.session.get_prompt(
                "interpret-page",
                {"focus": "navigation"}
            )
            prompt_messages = response.messages
            
            # Extract and print text content from prompt
            for message in prompt_messages:
                for content in message.content:
                    if content.type == "text":
                        preview = content.text[:200] + "..." if len(content.text) > 200 else content.text
                        print(f"Prompt text preview: {preview}")
                    elif content.type == "image":
                        print("Prompt includes image content")
            
            print("\n✅ All tests completed!")
            
        except Exception as e:
            print(f"\n❌ Error during tests: {e}")
            import traceback
            traceback.print_exc()
    
    async def cleanup(self):
        """Clean up resources"""
        print("\nCleaning up...")
        await self.exit_stack.aclose()
        print("Done!")

async def main():
    client = PlaywrightTestClient()
    try:
        await client.connect_to_server()
        await client.run_test_sequence()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())