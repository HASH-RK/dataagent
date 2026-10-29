# 技术点1: 处理不同类型的请求
# 技术点2：获取不同类型的参数
# 技术点3：使用路由器
# 技术点4：SSE流式响应
# 技术点5：生命周期
# 技术点6：中间件
# 技术点7：依赖注入
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.params import Depends
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.api.test.order_router import order_router
from app.api.test.product_router import product_router
from app.clients.es_client_manager import es_client_manager
from app.models.es.value_info_es import ValueInfoES
from app.repositories.es.value_es_repository import ValueESRepository


# 技术点5：应用的生命周期
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("在应用启动时执行， 一般执行一次性初始化操作，比如：初始化客户端")
    es_client_manager.init_client()
    yield
    print("在应用退出前执行, 一般执行一次性收尾工作，比如：关闭客户端")
    await es_client_manager.close()


# 创建应用
app = FastAPI(lifespan=lifespan)

# 技术点7：依赖注入
# 依赖注入：将依赖的对象注入进来 =》 手动和自动
# FastAPI的依赖注入：
    # 理解：将路由函数的依赖对象自动注入进来
    # 编码实现：定义接收依赖对象的形参,参数的默认值为Depends对象，同时给Depaends传入返回依赖对象的函数

# 接口功能：根据用户提交的keyword参数查询返回匹配的字段值信息列表
# 产生并返回依赖对象的函数
# 在路由处理请求前执行，返回的对象会自动赋值给对应的形参变量
def get_value_es_repo():
    print("get_value_es_repo()")
    return ValueESRepository(es_client_manager.client)
@app.get("/di")
async def test_di(keyword:str, value_es_repo:ValueESRepository=Depends(get_value_es_repo)):
    print("处理对/di的GET请求")
    value_infos: list[ValueInfoES] = await value_es_repo.search(keyword)
    return {"data": value_infos}




"""
测试6：中间件
"""
@app.middleware("http")
async def middleware_fun(request: Request, call_next):
    print("在路由处理请求前执行")  # 项目中会在此生成请求id并保存context对象中
    # 调用下一个中间件，如果没有了调用目标路由，得到路由执行返回的响应
    response = await call_next(request)
    print("在路由处理完请求后执行")
    # 返回响应给浏览器
    return response

# 技术点4：SSE流式响应
async def fake_stream():
    for i in range(10):
        yield 'data:{"msg": "abc"}\n\n'
        await asyncio.sleep(1)


async def test_call_generator():
    async for chunk in fake_stream():
        print("---", chunk)

@app.get("/sse")
def test_sse():
    print("处理对/sse的get请求")
    return StreamingResponse(fake_stream(), media_type="text/event-stream")




# 技术点3：使用路由器
# 什么情况下要用路由器？
    # 一个项目中包含多个功能模块，一个功能模块中包含多个接口
    # product模块：6  order模块：7  。。。。  接口的数量很多，放在一个文件中太大 =》应该分模块来管理对应模块的所有路由
    # 使用路由器来管理特定模块下的所有路由接口
# 什么路由器？
    # 管理多个路由的对象
# 什么是路由？
    # 就是一个后台接口，包含：请求方式、路由路径。路由函数（处理请求）
# 注册路由器
app.include_router(product_router, prefix="/v1")
app.include_router(order_router, prefix="/v2")

# 技术点2：获取不同类型的参数(文本)
"""
- 3种携带文本参数的方式
  - query参数：请求路径？后面的参数，如：/xxx?sex=male
  - path参数：看似像路径，与路由路径占位对应的部分，如：路由路径：/xxx/{id}，请求：/xxx/2
  - body参数：请求体参数，一般是json格式，如：{"name": "tom", "age": 12}
- 路由函数接收3种不同的参数
  - 接收 body参数：BaseModel子类型的形参
  - 接收path参数：与路由路径中占位同名的形参
  - 接收query参数：其它形参
"""

class BodyParams(BaseModel):
    name: str
    age: int

@app.post("/params/{id}")
def test_params(body_params: BodyParams, id: int, sex:str):
    print("处理对/params的POST请求", id, body_params.name, body_params.age, sex)

    return {"id":id, "name": body_params.name, "age":body_params.age, "sex": sex}


# 技术点1: 处理不同类型的请求
@app.get("/xxx")
def test_get():
    print("处理对/xxx的GET请求")
    return {"message": "get请求处理的返回数据..."}

@app.post("/xxx")
def test_get():
    print("处理对/xxx的POST请求")
    return {"message": "post请求处理的返回数据..."}

# 运行应用
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8001)
    # asyncio.run(test_call_generator())