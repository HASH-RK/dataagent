from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def execute_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义数据输出
    runtime.stream_writer({"stage": "执行SQL"})

    try:
        sql = state["sql"]
        dw_mysql_repo = runtime.context["dw_mysql_repo"]
        # 执行sql，查询dw库
        result = await dw_mysql_repo.execute_sql(sql)
        # 自定义数据输出
        runtime.stream_writer({"result": result})

        return {}  # 最后一个节点，不用返回数据
    except Exception as e:
        logger.error(f"执行SQL失败：{str(e)}")
        raise