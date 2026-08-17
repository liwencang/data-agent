from datetime import datetime

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger

# 星期几中文映射 weekday()返回0-6分别对应周一到周日
WEEKDAY_NAMES = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 流写入器
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "添加额外上下文信息", "status": "running"})
    try:
        # 1.当前日期信息：年月日、星期几、季度
        now = datetime.now()
        date_info = {
            "date": now.strftime("%Y-%m-%d"),
            "weekday": WEEKDAY_NAMES[now.weekday()],
            "quarter": f"第{(now.month - 1) // 3 + 1}季度",
        }

        # 2.数仓数据库信息：版本、方言
        dw_mysql_repository = runtime.context.dw_mysql_repository
        db_info = {
            "version": await dw_mysql_repository.get_db_version(),
            "dialect": dw_mysql_repository.get_db_dialect(),
        }

        writer({"type": "progress", "step": "添加额外上下文信息", "status": "success"})
        logger.info(f"添加额外上下文信息成功：date_info={date_info}, db_info={db_info}")
        # 3.更新state中日期信息和数据库信息
        return {"date_info": date_info, "db_info": db_info}
    except Exception as e:
        writer({"type": "progress", "step": "添加额外上下文信息", "status": "error"})
        logger.error(f"添加额外上下文信息失败, 错误信息: {str(e)}")
        raise
