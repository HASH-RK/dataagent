# 管理订单模块所有路由接口的路由器模块
from fastapi import APIRouter

# 创建路由器
order_router = APIRouter()

# 使用路由器来注册路由
@order_router.get("/order/xxx")
def test_get():
    print("处理对/order/xxx的GET请求")
    return {"content": "order模块的接口返回数据。。。"}