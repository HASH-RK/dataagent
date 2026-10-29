from elasticsearch import AsyncElasticsearch

from app.models.es.value_info_es import ValueInfoES

"""
用于操作es库的字段值数据的持久层模块
"""
class ValueESRepository:
    index_name = "data-agent-value_index2"
    mappings = {
        "dynamic": False,  # 静态映射
        "properties": {  # 字段
            "id": {"type": "keyword", "index": False},
            "value": {"type": "text", "analyzer": "ik_max_word"},
            "type": {"type": "keyword", "index": False},
            "column_id": {"type": "keyword", "index": False},
            "column_name": {"type": "keyword", "index": False},
            "table_id": {"type": "keyword", "index": False},
            "table_name": {"type": "keyword", "index": False},
        }
    }
    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    # 创建索引库
    async def create_index(self):
        client  = self.client
        index_name = self.index_name

        # 创建索引   如果存在先删除 => 方便多次测试
        if await client.indices.exists(index=index_name):
            await client.indices.delete(index=index_name)
        await client.indices.create(
            index=index_name,
            mappings=self.mappings
        )

    # 批量保存多个字段值信息列表
    async def insert_value_infos(self, value_infos:list[ValueInfoES]):
        # 创建索引   如果存在先删除
        await self.create_index()

        # 分批次保存数据
        batch_size = 50
        for i in range(0, len(value_infos), batch_size):
            batch_value_infos = value_infos[i:i+batch_size]

            # 根据value_infos收集生成operations
            operations = []
            for value_info in batch_value_infos:
                operations.append({
                    "index": {
                        "_index": self.index_name
                    }
                })
                operations.append(value_info)

            # 批量插入多个文档
            await self.client.bulk(
                operations = operations
            )

    # 搜索
    async def search(self, keyword:str)->list[ValueInfoES]:

        # 进行分词匹配查询
        result = await self.client.search(
            index=self.index_name,
            query={  # 根据value属性进行分词匹配查询
                "match": {
                    "value": keyword
                }
            },
        )

        # 读取数据
        # print(result)
        # print(result["hits"]["hits"][0]["_source"])
        return [ValueInfoES(**item["_source"]) for item in result["hits"]["hits"]]