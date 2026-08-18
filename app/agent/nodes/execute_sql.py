from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def execute_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 流写入器
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "执行SQL", "status": "running"})
    try:
        sql = state["sql"]
        dw_mysql_repository = runtime.context.dw_mysql_repository
        result = await dw_mysql_repository.execute_sql(sql)
        writer({"type": "result", "data": result})
        writer({"type": "progress", "step": "执行SQL", "status": "success"})
        logger.info(f"执行SQL成功, 返回{len(result)}行结果")
        logger.info(f"{result}")
    except Exception as e:
        writer({"type": "progress", "step": "执行SQL", "status": "error"})
        logger.error(f"执行SQL失败, 错误信息: {str(e)}")
        raise