import asyncio
import os

from agents import Agent, Runner
from agents.mcp import MCPServerSse

async def main():
    async with MCPServerSse(
        name="Cloudflare Bindings Server",
        params={
            "url": "https://bindings.mcp.cloudflare.com/sse",
            "headers": {
                "Authorization": f"Bearer {os.getenv('BINDINGS_SECRET')}"
            }
        }
    ) as server:
        agent = Agent(
            name="Assistant", 
            instructions="You are a helpful assistant. Use the tools available to you.",
            mcp_servers=[server]
        )

        # Direct tool call with OpenAPI spec
        list_tools = await server.list_tools()
        
        if isinstance(list_tools, list) and list_tools:
            for i, tool in enumerate(list_tools, 1):
                print(f"\n{i}. {tool}")
        else:
            print("No tools found")

        tool_result = await server.call_tool("accounts_list", {})
        print(f"Direct tool call result: {tool_result}")
        
        # You can also still use the agent if needed
        result = await Runner.run(starting_agent=agent, input="Call the accounts_list tool with an empty object to list my accounts.")
        print(f"Agent result: {result.final_output}")

if __name__ == "__main__":
    asyncio.run(main())
