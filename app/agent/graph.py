import asyncio

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agent.nodes.extract_keywords import extract_keywords
from app.agent.nodes.recall_column import recall_column
from app.agent.state import DataAgentState

builder = StateGraph(state_schema=DataAgentState)
builder.add_node("extract_keywords",extract_keywords)
builder.add_node("recall_column",recall_column)

builder.add_edge(START,"extract_keywords")
builder.add_edge("extract_keywords","recall_column")
builder.add_edge("recall_column",END)

graph = builder.compile()

if __name__ == "__main__":

    async def test_graph():
        async for chunk in graph.astream(DataAgentState(query="华北地区销售总额"),stream_mode="custom"):
            print(chunk)

    asyncio.run(test_graph())