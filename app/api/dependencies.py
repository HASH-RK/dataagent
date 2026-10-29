from fastapi.params import Depends

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_msyql_client_manager, meta_msyql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.query_service import QueryService

# 定义返回dw_session对象的函数
async def get_dw_session():
    assert dw_msyql_client_manager.session_factory
    async with dw_msyql_client_manager.session_factory() as session:
        # return session
        yield session

# 定义返回meta_session对象的函数
async def get_meta_session():
    assert meta_msyql_client_manager.session_factory
    async with meta_msyql_client_manager.session_factory() as session:
        # return session
        yield session


# 返回依赖（查询的业务对象）
def get_query_service(
    dw_session=Depends(get_dw_session),
    meta_session=Depends(get_meta_session),
):
    return QueryService(
        dw_mysql_repo=DWMysqlRepository(dw_session),
        meta_mysql_repo=MetaMysqlRepository(meta_session),
        value_es_repo=ValueESRepository(es_client_manager.client),
        column_qdrant_repo=ColumnQdrantRepository(qdrant_client_manager.client),
        metric_qdrant_repo=MetricQdrantRepository(qdrant_client_manager.client),
        embedding_client=embedding_client_manager.client
    )