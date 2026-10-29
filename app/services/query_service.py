import json

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.graph import compiled_graph
from app.agent.state import DataAgentState
from app.core.log import logger
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class QueryService:
    def __init__(
            self,
            dw_mysql_repo: DWMysqlRepository,
            meta_mysql_repo: MetaMysqlRepository,
            value_es_repo: ValueESRepository,
            column_qdrant_repo: ColumnQdrantRepository,
            metric_qdrant_repo: MetricQdrantRepository,
            embedding_client: HuggingFaceEndpointEmbeddings,

    ):
        self.dw_mysql_repo = dw_mysql_repo
        self.meta_mysql_repo = meta_mysql_repo
        self.value_es_repo = value_es_repo
        self.column_qdrant_repo = column_qdrant_repo
        self.metric_qdrant_repo = metric_qdrant_repo
        self.embedding_client = embedding_client

    # 搜索
    async def search(self, query:str):

        try:

            """
                - 华北地区销售总额
                - 2025年各地区平均销售额
                - 各个地区iPhone去年卖了多少钱
            """
            # 创建一个状态对象，作为初始状态
            state = DataAgentState(query=query, fail_count=0)
            # 创建一个上下文对象
            context = DataAgentContext(
                dw_mysql_repo=self.dw_mysql_repo,
                meta_mysql_repo=self.meta_mysql_repo,
                value_es_repo=self.value_es_repo,
                column_qdrant_repo=self.column_qdrant_repo,
                metric_qdrant_repo=self.metric_qdrant_repo,
                embedding_client=self.embedding_client
            )

            async for chunk in compiled_graph.astream(
                    input=state,
                    context=context,
                    stream_mode="custom",  # 执行得到是节点中指定的自定义输出
            ):
                # chunk: 节点执行的进度文本 / 查询得到列表数据
                # 通过yield不断向浏览器返回数据
                yield f'data: {json.dumps(chunk, ensure_ascii=False, default=str)} \n\n'

        except Exception as e:
            logger.error(f"搜索失败：{str(e)}")  # 需要返回给用户显示到前台
            # 通过yield向浏览器返回错误信息数据
            yield f'data: {json.dumps({"error": str(e)}, ensure_ascii=False, default=str)} \n\n'

            raise  # 抛出异常