# 管理产品模块所有路由接口的路由器模块
from fastapi import APIRouter

# 创建路由器
product_router = APIRouter()

# 使用路由器来注册路由
@product_router.get("/product/xxx")
def test_get():
    print("处理对/product/xxx的GET请求")
    return {"content": "product模块的接口返回数据。。。"}

# 后面可以注册当前模块的其它所有路由