from dataclasses import dataclass

from langchain_openai import OpenAIEmbeddings
from langgraph.types import StreamWriter

from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


@dataclass
class DataAgentContext:
    writer: StreamWriter
    dw_mysql_repository: DWMySQLRepository
    meta_mysql_repository: MetaMySQLRepository
    embedding_client: OpenAIEmbeddings
    value_es_repository: ValueESRepository
    column_qdrant_repository: ColumnQdrantRepository
    metric_qdrant_repository: MetricQdrantRepository
