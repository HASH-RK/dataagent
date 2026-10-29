import asyncio
from typing import Optional

from sqlalchemy import text, Select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession,async_sessionmaker
from app.conf.app_config import DBConfig, app_config
from app.models.mysql.table_info_mysql import TableInfoMySQL

"""
用来操作mysql数据库的客户端管理器模块
"""
class MysqlClientManager:
    def __init__(self, config: DBConfig):
        self.config = config
        self.client:Optional[AsyncEngine]  = None  # AsyncEngine|None
        self.session_factory:Optional[async_sessionmaker] = None

    def _get_url(self):
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}/{self.config.database}?charset=utf8mb4"

    def init_client(self):
        self.client = create_async_engine(
            self._get_url(),
            pool_size=10, # 连接池的大小，初始创建的常驻连接的个数
            max_overflow=5, # 能创建的临时连接的最大个数
            # 首先返回常驻连接，如果用满了，创建临时连接返回，如果用满了，等待指定的时间
            # 如果有常驻连接归还返回它，如果有临时连接释放，创建临时连接返回
            # 否则超时报错
        )
        # 创建会话工厂
        self.session_factory = async_sessionmaker(
            self.client, # 客户端对象
            autobegin=True,  # 自动开启事务  注意：事务需要手动提交或回滚
            autoflush=False,  # 是否将未提交的更新同步/刷新到暂存区（后面的查询是否可见）
        )

    async def close(self):
        await self.client.dispose()

# 创建针对dw库的客户端管理器
dw_msyql_client_manager = MysqlClientManager(app_config.db_dw)

# 创建针对meta库的客户端管理器
meta_msyql_client_manager = MysqlClientManager(app_config.db_meta)

if __name__ == '__main__':
    # 查询dw2库中的dim_customer表中的数据
    # 不用orm,自己写sql执行
    async def test():
        # 初始化客户端
        dw_msyql_client_manager.init_client()

        # 进行数据库表数据的查询
        # 创建会话
        # async with AsyncSession(
        #     dw_msyql_client_manager.client,
        #     autobegin=True, # 自动开启事务  注意：事务需要手动提交或回滚
        #     autoflush=False, # 是否将未提交的更新同步/刷新到暂存区（后面的查询是否可见）
        # ) as session:
        assert dw_msyql_client_manager.session_factory  # 断言有值
        async with dw_msyql_client_manager.session_factory() as session:
            # 执行sql
            sql = "select customer_name from dim_customer limit 2"
            result = await session.execute(text(sql))

            # 取出所有的数据
            """
            result.all(): 返回[row, row]  row对象是包含当前行所有字段值数据的可遍历的对象
            result.mappings().all(): 返回[RowMapping, RowMapping], RowMapping对象是包含当前行所有字段名和字段值数据的可遍历的对象
            result.scalars().all(): 返回[val, val], val是查询的第一个字段的值
            """
            # rows = result.all()
            # print(rows, type(rows), type(rows[0]))
            # for row in rows:
            #     for val in row:
            #         print(val)
            # print(rows[0].customer_name)

            # rows = result.mappings().all()
            # print(rows, type(rows), type(rows[0]))
            # for row in rows:
            #     for key, val in row.items():
            #         print(key, val)

            rows = result.scalars().all()
            print(rows, type(rows), type(rows[0]))
            for val in rows:
                print(val)



        # 关闭客户端
        await dw_msyql_client_manager.close()

    # 测试基于orm的添加和查询
    # 针meta2库中的table_info表进行测试
    async def test_orm():

        meta_msyql_client_manager.init_client()

        assert meta_msyql_client_manager.session_factory
        async with meta_msyql_client_manager.session_factory() as session:

            # 添加一条数据
            table_info1 = TableInfoMySQL(
                id="dim_customer1",
                name="dim_customer1",
                role="dim",
                description="客户信息维度表1"
            )
            session.add(table_info1)  # 内部insert 语句

            # 添加多条数据
            table_info2 = TableInfoMySQL(
                id="dim_customer2",
                name="dim_customer2",
                role="dim",
                description="客户信息维度表2"
            )
            table_info3 = TableInfoMySQL(
                id="dim_customer3",
                name="dim_customer3",
                role="dim",
                description="客户信息维度表3"
            )
            session.add_all([table_info2, table_info3])

            # 提交事务
            await session.commit()

            # 查询一条数据
            table_info = await session.get(TableInfoMySQL, "dim_customer1")  # select语句
            print(table_info, table_info.description)

            # 查询多条数据
            result = await session.execute(
                Select(TableInfoMySQL)
                    .limit(2)
            )

            table_infos:list[TableInfoMySQL] = result.scalars().all()  # [row, row]
            print(table_infos)

        await meta_msyql_client_manager.close()

    # 测试基于orm的更新和删除
    # 针meta2库中的table_info表进行测试
    async def test_orm2():
        meta_msyql_client_manager.init_client()

        assert meta_msyql_client_manager.session_factory
        async with meta_msyql_client_manager.session_factory() as session:
            # 更新
            table_info:TableInfoMySQL = await session.get(TableInfoMySQL, "dim_customer1")
            table_info.description = "aaa"

            # 删除
            await session.delete(table_info)

            # 提交事务
            await session.commit()

        await meta_msyql_client_manager.close()

    asyncio.run(test_orm2())