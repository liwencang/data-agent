from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 流写入器
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "合并召回信息", "status": "running"})
    try:
        pass
    except Exception as e:
        writer({"type": "progress", "step": "合并召回信息", "status": "error"})
        logger.error(f"合并召回信息失败, 错误信息: {str(e)}")
        raise