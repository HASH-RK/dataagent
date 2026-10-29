import uuid

import uvicorn
from fastapi import FastAPI, Request

from app.api.routers.query_router import search_router
from app.core.context import set_request_id
from app.core.lifespan import lifespan

# 创建app对象
app = FastAPI(lifespan=lifespan)

# 注册路由器
app.include_router(search_router)

# 利用请求中间件为每个请求保存一个唯一的请求id
@app.middleware("http")
async def middleware_fun(request: Request, call_next):
    # 生成请求id并保存context对象中
    set_request_id(str(uuid.uuid4()))
    # 调用目录路由处理请求，返回响应给浏览器
    return await call_next(request)

# 启动应用
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)