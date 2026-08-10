import asyncio
from typing import List

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from prompt import prompt_loader


async def recall_column(state:DataAgentState,runtime: Runtime[DataAgentContext]):
    # 流写入器
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "字段信息召回", "status": "running"})
    try:
        query = state["query"]
        # 1. 扩展查询
        logger.info("开始扩展查询")
        # 1.1 提示词
        prompt_text = prompt_loader.load_prompt("extend_keywords_for_column_recall")
        prompt = PromptTemplate(template=prompt_text,input_variables=["query"])
        # 1.2 大模型
        # 1.3 Json解析器
        parser = JsonOutputParser()
        chain = prompt | llm | parser
        result = chain.invoke({"query":query})
        logger.info(f"对原查询llm扩展后字段列表：{result}")

        # 2. 拼接查询关键词
        keywords = state["keywords"]
        keywords = list(set(keywords + result))
        logger.info(f"拼接现有关键词：{keywords}")

        # 3. 声明召回数组遍历查询，逐一添加
        column_qdrant_repository = runtime.context.column_qdrant_repository
        retrieved_column_dict:dict[str,ColumnInfo] = {}
        embedding_client = runtime.context.embedding_client
        for keyword in keywords:
            keyword_embedding = await embedding_client.aembed_query(keyword)
            column_infos:List[ColumnInfo] =  await column_qdrant_repository.search(keyword_embedding)
            for column_info in column_infos:
                if column_info.id not in retrieved_column_dict:
                    retrieved_column_dict[column_info.id] = column_info
        writer({"type": "progress", "step": "召回字段", "status": "success"})
        logger.info(f"召回字段成功：{list(retrieved_column_dict.keys())}")

        # 4. 结果写入到state
        return {"retrieved_columns": list(retrieved_column_dict.values())}
    except Exception as e:
        writer({"type": "progress", "step": "字段信息召回", "status": "error"})
        logger.error(f"字段信息召回失败, 错误信息: {str(e)}")
        raise
