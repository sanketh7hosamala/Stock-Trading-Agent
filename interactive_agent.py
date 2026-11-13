import asyncio
import sys
from pathlib import Path
from typing import TypedDict

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
)
from claude_agent_sdk.types import McpStdioServerConfig
from dotenv import load_dotenv
load_dotenv()
import os
k = os.getenv("ANTHROPIC_API_KEY")
print("key loaded:", bool(k), "| length:", len(k) if k else 0)

PROJECT_ROOT = Path(__file__).resolve().parent
EXIT_COMMANDS = {"exit", "quit", "bye"}
ALLOWED_TOOLS = [
    "mcp__Paper_Trading__get_stock_news",
    "mcp__Paper_Trading__get_stock_financials",
    "mcp__Paper_Trading__get_trade_recommendation",
    "mcp__Paper_Trading__execute_trade",
    "mcp__Paper_Trading__get_account",
    "mcp__Paper_Trading__get_positions",
    "mcp__Paper_Trading__get_order_status",
    "mcp__Paper_Trading__cancel_paper_order",
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
]

class ChatMessage(TypedDict):
    role: str
    content: str

def load_system_prompt() -> str:
    """Load the default system prompt from the project prompt folder."""
    prompt_path = PROJECT_ROOT / "prompts" / "system_instructions.md"
    return prompt_path.read_text(encoding="utf-8")

def format_history(conversation: list[ChatMessage]) -> str:
    """Render the history into a plain-text transcript for the model."""
    if not conversation:
        return ""
    return "\n\n".join(
        f"{entry['role'].capitalize()}: {entry['content']}" for entry in conversation
    )

async def run_chat() -> None:
    #yahoo_finance_server: McpStdioServerConfig = {
    #    "type": "stdio",
    #    "command": sys.executable,
    #    "args": [str(PROJECT_ROOT / "mcp_yahoo_finance.py")],
    #}
    system_prompt = load_system_prompt()
    conversation: list[ChatMessage] = []

    options = ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        system_prompt={"type": "custom", "prompt": system_prompt},
        mcp_servers={
            "Paper_Trading": {
                "type": "stdio",
                "command": "uv",
                "args": ["run", "trading-mcp.py"],
            }
        },
        allowed_tools=ALLOWED_TOOLS,
    )

    print("=== Claude PaperTrading Agent ===")
    print("Ask about a ticker, company fundamentals, price history, news, or analysts recommendations and execute paper trades.")
    print("Type 'exit' to end the conversation.")

    async with ClaudeSDKClient(options) as client:
        await client.connect()

        while True:
            user_input = input("\nUser: ").strip()

            if user_input.lower() in EXIT_COMMANDS:
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            await handle_user_turn(client, conversation, user_input)


async def handle_user_turn(
    client: ClaudeSDKClient, 
    conversation: list[ChatMessage], 
    user_input: str,
) -> None:
    """Handle a single user turn in the conversation, including previous context."""
    conversation.append({"role": "user", "content": user_input})
    transcript = format_history(conversation)
    prompt_text = (
        "You are continuing this conversation."
        "Use the earlier discussion as context to inform your response."
        f"{transcript}"
    )

    await client.query(prompt_text)
    
    print("\nAgent: ", end="", flush=True)
    assistant_text_parts: list[str] = []

    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
                    assistant_text_parts.append(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"\n-- Calling {block.name}...", end="", flush=True)
                elif isinstance(block, ToolResultBlock):
                    print(f"\n-- Tool response received.: {block.content}", end="", flush=True)
        
        elif isinstance(message, ResultMessage):
            if message.errors:
                print(f"\n-- Agent error: {message.errors}", end="", flush=True)
            if message.result and not assistant_text_parts:
                print(message.result, end="", flush=True)
                assistant_text_parts.append(message.result)

    if not assistant_text_parts:
        print("No text response was returned.", end="", flush=True)
    print("\n")
    
    full_reply = "".join(assistant_text_parts).strip()
    if full_reply:
        conversation.append({"role": "assistant", "content": full_reply})

    print("\n")

if __name__ == "__main__":
    #load_dotenv(PROJECT_ROOT / ".env")
    asyncio.run(run_chat())
