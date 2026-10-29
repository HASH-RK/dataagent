# 生命周期函数
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_msyql_client_manager, dw_msyql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化客户端
    embedding_client_manager.init_client()
    qdrant_client_manager.init_client()
    es_client_manager.init_client()
    dw_msyql_client_manager.init_client()
    meta_msyql_client_manager.init_client()

    yield
    # 关闭客户端
    await qdrant_client_manager.close()
    await es_client_manager.close()
    await dw_msyql_client_manager.close()
    await meta_msyql_client_manager.close()