import asyncio
from uuid import uuid4

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

mcp_adapter = MCPAdapter("http://127.0.0.1:8000/mcp")


async def main():
    async with mcp_adapter:
        tools = await mcp_adapter.list_tools()

        agent = create_agent(
            model="claude-haiku-4-5",
            tools=tools,
            system_prompt="You are a helpful task management assistant",
            checkpointer=InMemorySaver(),
        )

        config = {"configurable": {"thread_id": str(uuid4())}}

        human_question = "Can you help me ?"

        while human_question != "q":
            print("Agent response: ")

            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=human_question)]}, config=config
            )

            print(result["messages"][-1].text)

            human_question = input("Human message (q to exit): \n\n")


if __name__ == "__main__":
    asyncio.run(main())
