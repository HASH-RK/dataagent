from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

"""
用于操作mysql的dw库数据的持久层模块
"""
class DWMysqlRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # 查询指定表的所有字段的类型：dict[字段名，字段类型]
    async def get_column_types(self, table_name:str)->dict[str, str]:
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        return {item.Field:item.Type for item in result.all()}

    # 查询指定表中的指定字段的指定数量的字段值, 默认10个
    async def get_column_values(self, table_name:str, column_name:str, limit:int=10)->list:
        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        result = await self.session.execute(text(sql))
        return result.scalars().all()  # [val, val]

    # 得到数据库信息  {"dialect": "mysql", "version": "1.2.3"}
    async def get_db_info(self)->dict[str, str]:
        # 版本
        result = await self.session.execute(text("select version()"))
        version:str = result.scalar()
        # 名称
        dialect = self.session.bind.dialect.name

        return {"version": version, "dialect": dialect}

    # 校验sql语法
    async def validate_sql(self, sql: str):
        await self.session.execute(text(f"explain {sql}"))
        # 模拟校验SQL失败
        # raise Exception("SQL中可能包含不存在的字段")

    # 执行指定的查询SQL
    async def execute_sql(self, sql:str)->list:
        result = await self.session.execute(text(sql))

        # return result.mappings().all()  # [rowMapping, rowMapping]  字段名和字段值的列表
        return [dict(item) for item in result.mappings().all()]  # [rowMapping, rowMapping]  字典的列表 =》 json