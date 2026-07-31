import asyncio
from typing import Optional

from elasticsearch import AsyncElasticsearch

from app.conf.app_config import ESConfig, app_config


class ElasticsearchClientManager:
    def __init__(self, config: ESConfig):
        self.config = config
        self.client: Optional[AsyncElasticsearch] = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncElasticsearch(hosts=self._get_url())

    async def close(self):
        if self.client:
            await self.client.close()


if __name__ == "__main__":
    async def test():

        es_manager = ElasticsearchClientManager(app_config.es)
        es_manager.init()
        es_client = es_manager.client
        if not es_client:
            return

        mappings = {
            "dynamic": False,
            "properties": {
                "name": {"type": "text", "analyzer": "ik_max_word"},
                "author": {"type": "text", "analyzer": "ik_max_word"},
                "release_date": {"type": "date", "format": "yyyy-MM-dd"},
                "page_count": {"type": "integer"}
            }
        }

        await es_client.indices.create(index="books", mappings=mappings)

        operations = [
            {"index": {"_index": "books"}},
            {"name": "三体", "author": "刘慈欣", "release_date": "2000-03-15", "page_count": 585},
            {"index": {"_index": "books"}},
            {"name": "平凡的时间", "author": "路遥", "release_date": "1985-06-01", "page_count": 328},
            {"index": {"_index": "books"}},
            {"name": "活着", "author": "余华", "release_date": "1953-10-15", "page_count": 227},
            {"index": {"_index": "books"}},
            {"name": "我与地坛", "author": "史铁生", "release_date": "1932-06-01", "page_count": 268}
        ]

        await es_client.bulk(
            index="books",
            operations=operations
        )
        await es_manager.close()

    asyncio.run(test())
