from dataclasses import asdict
from typing import List, Dict, Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

from app.conf.app_config import app_config
from app.entities.column_info import ColumnInfo


class ColumnQdrantRepository:
    coll_name = "data-agent-column"

    def __init__(self, qd_client: AsyncQdrantClient):
        self.client = qd_client

    async def ensure_collection(self):
        if not await self.client.collection_exists(collection_name=self.coll_name):
            await self.client.create_collection(
                collection_name=self.coll_name,
                vectors_config=VectorParams(
                    size=app_config.qdrant.embedding_size,
                    distance=Distance.COSINE
                )
            )

    async def upsert(self, ids: List[Any], embeddings: List[List[float]], payloads: List[ColumnInfo], batch_size: int):
        zipped = list(zip(ids, embeddings, payloads))
        for i in range(0, len(zipped), batch_size):
            batch = zipped[i:i + batch_size]
            points = [PointStruct(
                id=id,
                vector=embedding,
                payload=asdict(payload)
            )
                for id, embedding, payload in batch]
            await self.client.upsert(collection_name=self.coll_name,points=points)
