import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, MetricInfoStata
from app.core.log import logger
from prompt.prompt_loader import load_prompt


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 流写入器
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤指标信息", "status": "running"})
    try:
        # 大模型分析需要的指标信息
        query = state['query']
        metric_infos:list[MetricInfoStata] = state['metric_infos']
        metric_infos_yaml = yaml.dump(metric_infos,allow_unicode=True,sort_keys=False)
        prompt_text = load_prompt("filter_metric_info")
        prompt =PromptTemplate(template=prompt_text,input_variables=['query','metric_infos'])
        parser = JsonOutputParser()
        chain = prompt | llm | parser
        result = await chain.ainvoke({"query":query,"metric_infos":metric_infos_yaml})

        # 过滤掉无用的指标
        for metric_info in metric_infos[:]:
            if metric_info['name'] not in result:
                metric_infos.remove(metric_info)

        logger.info(f"过滤后指标信息：{[metric_info['name'] for metric_info in metric_infos]}")
        return {"metric_infos": metric_infos}

    except Exception as e:
        writer({"type": "progress", "step": "过滤指标信息", "status": "error"})
        logger.error(f"过滤指标信息失败, 错误信息: {str(e)}")
        raise
if __name__ == "__main__":
    # class MetricInfoStata(TypedDict):
    #     name: str
    #     description: str
    #     relevant_columns: list[str]
    #     alias: list[str]
    metric_info = MetricInfoStata(
        name="filter_metric_info",
        description="你好",
        relevant_columns=['abc','吃了吗'],
        alias=['河北','广东']
    )
    print(yaml.dump(metric_info,allow_unicode=True,sort_keys=False))