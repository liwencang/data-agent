import asyncio

from langgraph.config import get_stream_writer

from app.agent.state import DataAgentState
from app.core.log import logger


async def recall_column(state:DataAgentState):
    writer = get_stream_writer()

    # logger.info(state["query"])
    logger.info("召回字段信息")
    writer({"type": "progress", "step": "召回字段信息", "status": "running"})
    await asyncio.sleep(2)
    writer({"type": "progress", "step": "召回字段信息", "status": "success"})
