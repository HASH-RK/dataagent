import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


# 利用大模型来进行校正， 传入哪些数据呢？ table_infos/metric_infos/date_info/db_info/query + 错误SQL + 错误的原因error
async def correct_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义数据输出
    runtime.stream_writer({"stage": "校正SQL"})

    try:
        # 取出相关数据
        table_infos = state["table_infos"]
        metric_infos = state["metric_infos"]
        date_info = state["date_info"]
        db_info = state["db_info"]
        query = state["query"]
        sql = state["sql"]
        error = state["error"]

        # 使用大模型生成sql
        prompt_tempalate = PromptTemplate(
            template=load_prompt("correct_sql"),
            input_variables=["query", "table_infos", "metric_infos", "date_info", "db_info", "sql", "error"]
        )
        output_parser = StrOutputParser()
        chain = prompt_tempalate | llm | output_parser
        sql: str = await chain.ainvoke({
            "query": query,
            "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
            "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False),
            "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False),
            "sql": sql,
            "error": error,
        })

        logger.info(f"校正SQL完成：{sql}")
        return {"sql": sql}  # 自动跳转到validate_sql节点
    except Exception as e:
        logger.error(f"校正SQL失败：{str(e)}")
        raise