"""Chat in the terminal with a Claude agent that manages tasks through MCP.

``client.py`` decides which tool to call in fixed code. Here, the model decides.
You can type "add a high priority task to write tests", and the agent chooses
``create_task`` and its arguments. For each message, the agent loop is:

1. Send the conversation and the tool definitions to the model.
2. If the model asks for a tool, call that tool on the MCP server and add the
   result to the conversation. Then go back to step 1.
3. If the model answers with text, return that answer.

To run this script, you need ``ANTHROPIC_API_KEY`` in the ``.env`` file. Start
the server in another terminal, and then run::

    uv run python -m mcp_server.langchain_client

Each model call uses your Anthropic API credits.
"""

import asyncio
from uuid import uuid4

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

# Copy the values in .env into environment variables. The Anthropic client reads
# ANTHROPIC_API_KEY from the environment. The key stays out of the source code,
# and .gitignore keeps .env out of Git.
load_dotenv()

# The adapter connects to the MCP server and converts its tools into a form that
# a LangChain agent can call.
mcp_adapter = MCPAdapter("http://127.0.0.1:8000/mcp")


async def main():
    """Connect to the MCP server, build the agent, and run the chat loop.

    The loop ends when the user types ``q``. The conversation history is lost
    when the program exits, but tasks stay in the database.
    """
    # The connection must stay open for the whole chat, because the agent calls
    # the tools through it. All the code below is inside this block.
    async with mcp_adapter:
        tools = await mcp_adapter.list_tools()

        agent = create_agent(
            model="claude-haiku-4-5",
            tools=tools,
            system_prompt="You are a helpful task management assistant",
            # The checkpointer saves the messages of each conversation in
            # memory. Without it, the agent forgets earlier messages.
            checkpointer=InMemorySaver(),
        )

        # The checkpointer finds saved messages by thread_id. A new random ID
        # starts a new conversation, and reusing the ID continues the same one.
        config = {"configurable": {"thread_id": str(uuid4())}}

        # The first message is fixed, so the agent speaks before the user types.
        human_question = "Can you help me ?"

        while human_question != "q":
            print("Agent response: ")

            # ainvoke runs the whole agent loop, including any tool calls. Send
            # only the new message, because the checkpointer adds the history.
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=human_question)]}, config=config
            )

            # The last message in the conversation is the model's final answer.
            print(result["messages"][-1].text)

            # input() blocks the event loop. That is safe here because this
            # program has no other work to run while it waits for the user.
            human_question = input("Human message (q to exit): \n\n")


if __name__ == "__main__":
    asyncio.run(main())
