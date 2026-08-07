from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 流写入器
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "指标信息召回", "status": "running"})
    try:
        pass
    except Exception as e:
        writer({"type": "progress", "step": "指标信息召回", "status": "error"})
        logger.error(f"指标信息召回失败, 错误信息: {str(e)}")
        raise