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

1. 利用大模型对表和字段信息进行过滤，返回包含需要的表名和字段组组成的字典 
    {
        "表名1":["字段1", "字段2", "..."],
        "表名2":["字段1", "字段2", "..."]
    }
2. 对table_infos过滤掉不需要的表信息和字段信息
3. 返回过滤后table_infos
"""
async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义数据输出
    runtime.stream_writer({"stage": "过滤表和字段"})

    try:
        query = state["query"]
        table_infos = state["table_infos"]


        # 1. 利用大模型对表和字段信息进行过滤，返回包含需要的表名和字段组组成的字典
        prompt_tempalate = PromptTemplate(
            template=load_prompt("filter_table_info"),
            input_variables=["query","table_infos"]
        )
        output_parser = JsonOutputParser()
        chain = prompt_tempalate | llm | output_parser
        result: dict[str, list[str]] = await chain.ainvoke({
            "query": query,
            "table_infos": yaml.dump(
                table_infos,
                allow_unicode=True, # 保留中文原文，不转换为unicode编码  ‘\u5317\u4eac’
                sort_keys=False, # 不要对数据中的字典中的属性进行排序，保持原来的顺序
            )
        })

        # 2. 对table_infos过滤掉不需要的表信息和字段信息
        # 问题：遍历数组时删除数据元素可能会漏掉被删除的下一个元素
        # 解决：遍历浅拷贝的数组，删除原数组元素
        for table_info in table_infos[:]:
            table_name = table_info["name"]
            if table_name not in result:
                table_infos.remove(table_info) # 过滤表信息
            else:  # 留下表信息，下面就进行字段过滤
                for column in table_info["columns"][:]: # 也要浅拷贝
                    column_name = column["name"]
                    column_names = result[table_name]
                    if column_name not in column_names:
                        table_info["columns"].remove(column)  # 过滤字段信息

        logger.info(f"过滤表和字段完成：{table_infos}")
        # 3. 返回过滤后table_infos
        return {"table_infos": table_infos}
    except Exception as e:
        logger.error(f"过滤表和字段失败：{str(e)}")
        raise