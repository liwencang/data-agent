import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from prompt.prompt_loader import load_prompt


async def correct_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "校正SQL", "status": "running"})
    try:
        # 从state中获取上下文信息
        query = state["query"]
        table_infos = state["table_infos"]
        metric_infos = state["metric_infos"]
        date_info = state["date_info"]
        db_info = state["db_info"]
        sql = state["sql"]
        error = state["error"]

        # 将上下文信息序列化为YAML格式
        table_infos_yaml = yaml.dump(table_infos, allow_unicode=True, sort_keys=False)
        metric_infos_yaml = yaml.dump(metric_infos, allow_unicode=True, sort_keys=False)
        date_info_yaml = yaml.dump(date_info, allow_unicode=True, sort_keys=False)
        db_info_yaml = yaml.dump(db_info, allow_unicode=True, sort_keys=False)

        # 加载提示词并构建链
        prompt_text = load_prompt("correct_sql")
        prompt = PromptTemplate(
            template=prompt_text,
            input_variables=["table_infos", "metric_infos", "date_info", "db_info", "query", "sql", "error"]
        )
        parser = StrOutputParser()
        chain = prompt | llm | parser

        # 调用大模型校正SQL
        corrected_sql = await chain.ainvoke({
            "table_infos": table_infos_yaml,
            "metric_infos": metric_infos_yaml,
            "date_info": date_info_yaml,
            "db_info": db_info_yaml,
            "query": query,
            "sql": sql,
            "error": error,
        })

        # 清理可能的Markdown代码块标记
        corrected_sql = corrected_sql.strip()
        if corrected_sql.startswith("```sql"):
            corrected_sql = corrected_sql[6:]
        elif corrected_sql.startswith("```"):
            corrected_sql = corrected_sql[3:]
        if corrected_sql.endswith("```"):
            corrected_sql = corrected_sql[:-3]
        corrected_sql = corrected_sql.strip()

        logger.info(f"校正SQL成功：{corrected_sql}")
        writer({"type": "progress", "step": "校正SQL", "status": "success"})
        return {"sql": corrected_sql, "error": None}
    except Exception as e:
        writer({"type": "progress", "step": "校正SQL", "status": "error"})
        logger.error(f"校正SQL失败, 错误信息: {str(e)}")
        raise
