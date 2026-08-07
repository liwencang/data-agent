from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 流写入器
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤表信息", "status": "running"})
    try:
        pass
    except Exception as e:
        writer({"type": "progress", "step": "过滤表信息", "status": "error"})
        logger.error(f"过滤表信息失败, 错误信息: {str(e)}")
        raise