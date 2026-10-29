import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt

"""

1. 利用大模型对指标信息进行过滤，返回包含需要的指标名组成的数组
    ["指标1", "指标2", "..."]
2. 对metric_infos过滤掉不需要的指标信息
3. 返回过滤后metric_infos
"""
async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义数据输出
    runtime.stream_writer({"stage": "过滤指标"})

    try:
        query = state["query"]
        metric_infos = state["metric_infos"]


        # 1. 利用大模型对指标信息进行过滤，返回包含需要的指标名组成的数组
        prompt_tempalate = PromptTemplate(
            template=load_prompt("filter_metric_info"),
            input_variables=["query","metric_infos"]
        )
        output_parser = JsonOutputParser()
        chain = prompt_tempalate | llm | output_parser
        result: list[str] = await chain.ainvoke({
            "query": query,
            "metric_infos": yaml.dump(
                metric_infos,
                allow_unicode=True, # 保留中文原文，不转换为unicode编码  ‘\u5317\u4eac’
                sort_keys=False, # 不要对数据中的字典中的属性进行排序，保持原来的顺序
            )
        })

        # 2. 对metric_infos过滤掉不需要的指标信息
        # 问题：遍历数组时删除数据元素可能会漏掉被删除的下一个元素
        # 解决：遍历浅拷贝的数组，删除原数组元素
        for metric_info in metric_infos[:]:
            metric_name = metric_info["name"]
            if metric_name not in result:
                metric_infos.remove(metric_info) # 过滤指标信息


        logger.info(f"过滤指标完成：{metric_infos}")
        # 3. 返回过滤后metric_infos
        return {"metric_infos": metric_infos}
    except Exception as e:
        logger.error(f"过滤指标失败：{str(e)}")
        raise