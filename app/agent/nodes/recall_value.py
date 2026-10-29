from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.models.es.value_info_es import ValueInfoES
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.prompt.prompt_loader import load_prompt

"""
1. 使用大模型对query语义化提取关键词列表，与前面jieba提取关键词进行去重合并 =》 keywords:list[str]
2. 遍历每个关键词，去ES中匹配出一个字段值信息列表， 并进行去重合并 =》 recall_values: list[ValueInfoES]
4. 返回recall_values
"""
async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义数据输出
    runtime.stream_writer({"stage": "召回字段值"})

    try:
        query = state["query"]
        keywords = state["keywords"]
        value_es_repo = runtime.context["value_es_repo"]

        # 1. 使用大模型对query语义化提取关键词列表，与前面jieba提取关键词进行去重合并 =》 keywords:list[str]
        prompt_tempalate = PromptTemplate(
            template=load_prompt("extend_keywords_for_value_recall"),
            input_variables=["query"]
        )
        output_parser = JsonOutputParser()
        chain = prompt_tempalate | llm | output_parser
        result: list[str] =  await chain.ainvoke({"query": query})
        logger.info(f"recall_value llm keywords={result}")
        keywords = list(set(keywords + result))

        # 2. 遍历每个关键词，去ES中匹配出一个字段值信息列表， 并进行去重合并 =》 recall_values: list[ValueInfoES]
        value_infos_dict: dict[str, ValueInfoES] = {}
        for keyword in keywords:
            value_infos:list[ValueInfoES] = await value_es_repo.search(keyword)
            for value_info in value_infos:
                value_infos_dict[value_info["id"]] = value_info  # 如果重复就覆盖了
        # 生成列表
        recall_values = list(value_infos_dict.values())

        logger.info(f"召回字段值完成： {recall_values}")

        # 4. 返回recall_values
        return {"recall_values": recall_values}
    except Exception as e:
        logger.error(f"召回字段值失败：{str(e)}")
        raise