from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def execute_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 流写入器
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "执行SQL", "status": "running"})
    try:
        pass
    except Exception as e:
        writer({"type": "progress", "step": "执行SQL", "status": "error"})
        logger.error(f"执行SQL失败, 错误信息: {str(e)}")
        raise
