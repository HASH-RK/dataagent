import asyncio
from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime

from app.repositories.es.value_es_repository import ValueESRepository



"""
langgraph相关重要概念
    状态图：StateGraph的实例
    节点：实现特定功能的函数
    状态：包含多个可变数据的对象，在图的各个节点上传递
    上下文：包含多个不可变数据的对象，在图的各个节点上传递
    边： 它是A->B2个节点的连线, A执行后执行B，且将最新的状态数据传递给B
节点函数的参数：
    state: 状态对象   自定义类型
    runtime: Runtime  运行时对象，包含:
        stream_writer: 向调用者输出自定义数据的函数
        store:实现跨会话长期记忆的对象，默认是保存在内存中
        context: 包含固定数据或依赖的外部模块的对象   自定义类型
    config：ConfigRunnable 保存配置的对象，比如执行时指定的thread_id
stream_mode:
    updates: 外部得到是节点返回的更新
    values: 外部得到是节点返回后合并后的state值
    custom: 外部得到是stream_writer指定的自定义数据
"""

# 自定义状态类型
# state包含的是一些可变的数据，它们在节点间不断传递
class MyState(TypedDict):
    query:str # 用户提问
    keywords: list[str] # 提取的关键词列表
    sql: str # 生成SQL

# 自定义上下文类型
# context包含的一些不可变的数据（很可能是节点需要使用的一些模块对象）,在节点间不断传递
class MyContext(TypedDict):
    db_name:str
    value_es_repo: ValueESRepository

# db_name="dw"

# 节点函数
def extract_keywords(state: MyState, runtime: Runtime[MyContext], config: RunnableConfig):


    print(runtime)
    print(runtime.context["db_name"])
    print(config)

    # 自定义输出数据内容
    runtime.stream_writer("提取关键词")


    query = state["query"]
    print(f"提取关键词， query={query}")
    keywords:list[str] = ["你", "是", "谁"]

    # 返回状态更新， 不要直接更新状态 ->后面graph会自动将返回的更新合并到state,并传递下一个节点
    # state["keywords"] = keywords
    return {"keywords": keywords}

def generate_sql(state: MyState, runtime: Runtime):
    # 自定义输出数据内容
    runtime.stream_writer("生成SQL")

    keywords = state["keywords"]
    print(f"生成SQL, keywords={keywords}")

    sql = "select * from xxx"

    return {"sql": sql}


# 创建状态图
state_graph = StateGraph(
    state_schema=MyState,  # 状态类型
    context_schema=MyContext, # 上下文类型
)

# 添加节点
state_graph.add_node("extract_keywords", extract_keywords)
state_graph.add_node("generate_sql", generate_sql)

# 添加边
state_graph.add_edge(START, "extract_keywords")
state_graph.add_edge("extract_keywords", "generate_sql")
state_graph.add_edge("generate_sql", END)

# 编译图
compiled_graph = state_graph.compile()

# 运行
if __name__ == '__main__':
    async def test():
        # 创建一个状态对象，作为初始状态
        state = MyState(query="你是谁？")
        # 创建一个上下文对象
        context = MyContext(db_name="dw")

        async for chunk in compiled_graph.astream(
            input=state,
            context=context,
            # stream_mode="updates"  # 执行得到的是每个节点返回的状态更新  默认
            # stream_mode="values"  # 执行得到的是节点返回合并后state的值
            stream_mode="custom",  # 执行得到是节点中指定的自定义输出
            config={"configurable": {"thread_id": "thread-1"}}
        ):
            print("---", chunk)

    asyncio.run(test())
