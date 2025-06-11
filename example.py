import asyncio
import os

from agents import Agent, Runner
from agents.mcp import MCPServerSse
from openai import OpenAI

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
        print(f"Agent result: {result.final_output}", end='\n\n')

        client = OpenAI()

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Call the accounts_list tool with an empty object to list my accounts."}
                ],
                # This will fail because the tools list does not conform to openai format
                tools=list_tools
            )
            print(f"OpenAI response: {response}")
        except Exception as e:
            print(f"Expected Error: {e}", end='\n\n')
        
        # How users would then try to format it
        formatted_tools = []
        for tool in list_tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    # This would fail because accounts_list has an inputSchema like
                    # { type: 'object' } instead of just being null itself
                    "parameters": tool.inputSchema
                }
            })

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Call the accounts_list tool with an empty object to list my accounts."}
                ],
                # This will also fail
                tools=formatted_tools
            )
            print(f"OpenAI response: {response}")
        except Exception as e:
            print(f"Expected Error: {e}", end='\n\n')

        # How users should format it
        formatted_tools = []
        for tool in list_tools:
            # If properties is empty then don't send the parameters themselves
            if "properties" not in tool.inputSchema:
                formatted_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description
                    }
                })
            else:
                formatted_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Call the accounts_list tool with an empty object to list my accounts."}
                ],
                # This will now pass
                tools=formatted_tools
            )
            print(f"Working OpenAI response: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
