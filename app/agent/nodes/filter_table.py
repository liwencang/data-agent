import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, TableInfoState
from app.core.log import logger
from prompt.prompt_loader import load_prompt


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 流写入器
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤表信息", "status": "running"})
    try:
        # 大模型分析需要的表信息
        query = state['query']
        table_infos: list[TableInfoState] = state['table_infos']
        table_infos_yaml = yaml.dump(table_infos, allow_unicode=True, sort_keys=False)
        prompt_text = load_prompt("filter_table_info")
        prompt = PromptTemplate(template=prompt_text, input_variables=['query', 'table_infos'])
        parser = JsonOutputParser()
        chain = prompt | llm | parser
        result = await chain.ainvoke({"query": query, "table_infos": table_infos_yaml})

        # 过滤掉无用的表和字段
        for table_info in table_infos[:]:
            table_name = table_info['name']
            if table_name not in result:
                table_infos.remove(table_info)
                continue
            selected_columns = result[table_name]
            for column in table_info['columns'][:]:
                if column['name'] not in selected_columns:
                    table_info['columns'].remove(column)
        writer({"type": "progress", "step": "过滤表信息", "status": "success"})
        logger.info(f"过滤后表信息：{[table_info['name'] for table_info in table_infos]}")
        return {"table_infos": table_infos}

    except Exception as e:
        writer({"type": "progress", "step": "过滤表信息", "status": "error"})
        logger.error(f"过滤表信息失败, 错误信息: {str(e)}")
        raise