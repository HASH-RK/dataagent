from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger

MAX_FAIL_COUNT = 5 # 最大失败次数

# 利用explain对sql的语法进行校验，能检查：表名、字段名、关键字是否正确
async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):

    # 一上来就检查失败次数是否达到最大限制 =》 抛出错误
    if state["fail_count"] == MAX_FAIL_COUNT:
        raise Exception("生成的SQL校验失败次数已达到最大值")

    # 自定义数据输出
    runtime.stream_writer({"stage": "校验SQL"})

    try:
        sql = state["sql"]
        dw_mysql_repo = runtime.context["dw_mysql_repo"]

        # 利用explain对sql的语法进行校验，
        await dw_mysql_repo.validate_sql(sql)
        logger.info("校验SQL通过")
        return {"error": None} # 自动跳转到execute_sql节点
    except Exception as e:
        logger.error(f"校验SQL失败：{str(e)}")

        # 校验失败，fail_count要加1

        # 返回带error数据的状态更新
        return {"error": f"校验SQL失败：{str(e)}", "fail_count": state["fail_count"]+1} # 自动跳转到correct_sql节点