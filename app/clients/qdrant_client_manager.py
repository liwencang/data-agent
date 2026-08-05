import asyncio
from typing import Optional

from pydantic import StrictStr
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct, Filter, Condition, FieldCondition, MatchValue

from app.clients.embedding_client_manager import EmbeddedClientManager
from app.conf.app_config import QdrantConfig, app_config


class QdrantClientManager:
    def __init__(self, config: QdrantConfig):
        self.config: QdrantConfig = config
        self.client: Optional[AsyncQdrantClient] = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncQdrantClient(url=self._get_url())

    async def close(self):
        if self.client:
            await self.client.close()


if __name__ == "__main__":
    collection_name = "test_collection"
    q_manager = QdrantClientManager(app_config.qdrant)
    embedding_manager = EmbeddedClientManager(app_config.embedding)
    embedding_manager.init()
    q_manager.init()

    embeddings = embedding_manager.embeddings
    q_client = q_manager.client


    async def test():
        if q_client is None or embeddings is None:
            print("embedding is None or QdrantClient is None")
            return

        exists = await q_client.collection_exists(collection_name="test_collection")

        if not exists:
            await q_client.create_collection(
                collection_name="test_collection",
                vectors_config=VectorParams(
                    size=app_config.qdrant.embedding_size,
                    distance=Distance.COSINE
                )
            )
        keywords = [
            # 水果
            "苹果", "香蕉", "橙子", "葡萄", "草莓", "西瓜", "芒果", "榴莲", "樱桃", "猕猴桃",
            # 英雄联盟英雄
            "亚索", "劫", "卡莎", "阿狸", "盖伦", "瑞兹", "盲僧", "德莱文", "拉克丝", "永恩",
            # IT职业
            "前端开发", "后端开发", "测试工程师", "运维工程师", "算法工程师", "数据分析师", "产品经理", "UI设计师",
            "AI工程师", "网络工程师",
            # 编程语言
            "Python", "Java", "Go", "C++", "JavaScript", "TypeScript", "Rust", "PHP", "C#", "SQL",
            # 交通工具
            "汽车", "高铁", "飞机", "自行车", "摩托车", "轮船", "地铁", "大巴", "电车", "跑车",
            # 动物
            "猫", "狗", "老虎", "熊猫", "狮子", "兔子", "大象", "海豚", "老鹰", "松鼠"
        ]

        points = [PointStruct(
            id=index,
            vector=await embeddings.aembed_query(keyword),
            payload={"keyword": keyword}
        ) for index, keyword in enumerate(keywords)]

        # res = await q_client.upsert(
        #     collection_name="test_collection",
        #     points=points,
        # )
        query = "汽车"
        query_embedding = await embeddings.aembed_query(query)
        res = await q_client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            score_threshold=0.3,
            query_filter=Filter(must=FieldCondition(key="keyword",match=MatchValue(value=StrictStr("飞机"))))

        )
        keyword_list = [point.payload['keyword'] for point in res.points]
        print(keyword_list)
    asyncio.run(test())
