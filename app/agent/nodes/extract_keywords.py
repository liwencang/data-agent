import asyncio

from langgraph.config import get_stream_writer

from app.agent.state import DataAgentState
from app.core.log import logger


async def extract_keywords(state:DataAgentState):
    # logger.info(state["query"])
    logger.info("抽取关键信息")
    writer = get_stream_writer()
    writer({"type": "progress", "step": "抽取关键信息", "status": "running"})
    await asyncio.sleep(2)
    writer({"type": "progress", "step": "抽取关键信息", "status": "success"})