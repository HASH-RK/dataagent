# 搜索的路由器
from fastapi import APIRouter
from fastapi.params import Depends
from starlette.responses import StreamingResponse

from app.api.dependencies import get_query_service
from app.api.schemas.query_schema import QuerySchema
from app.services.query_service import QueryService

# 创建路由器
search_router = APIRouter()

# 注册路由
@search_router.post("/api/query")
def query(body_params: QuerySchema, query_service:QueryService=Depends(get_query_service)):
    # 返回流式响应对象
    return StreamingResponse(query_service.search(body_params.query), media_type="text/event-stream")