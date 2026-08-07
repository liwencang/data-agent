import asyncio

from langgraph.config import get_stream_writer
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.context import DataAgentContext
from app.agent.nodes.extract_keywords import extract_keywords
from app.agent.nodes.recall_column import recall_column
from app.agent.state import DataAgentState
from app.clients.elasticsearch_client_manager import ElasticsearchClientManager
from app.clients.embedding_client_manager import EmbeddedClientManager
from app.clients.mysql_client_manager import MysqlClientManager
from app.clients.qdrant_client_manager import QdrantClientManager
from app.conf.app_config import app_config
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository

builder = StateGraph(state_schema=DataAgentState)
builder.add_node("extract_keywords", extract_keywords)
builder.add_node("recall_column", recall_column)

builder.add_edge(START, "extract_keywords")
builder.add_edge("extract_keywords", "recall_column")
builder.add_edge("recall_column", END)

graph = builder.compile()

if __name__ == "__main__":

    async def test_graph():
        dw_client_manager = MysqlClientManager(app_config.db_dw)
        meta_client_manager = MysqlClientManager(app_config.db_meta)
        qdrant_client_manager = QdrantClientManager(app_config.qdrant)
        embedding_client_manager = EmbeddedClientManager(app_config.embedding)
        es_client_manager = ElasticsearchClientManager(app_config.es)

        dw_client_manager.init()
        meta_client_manager.init()
        qdrant_client_manager.init()
        embedding_client_manager.init()
        es_client_manager.init()

        dw_session_factory = dw_client_manager.session_factory
        meta_session_factory = meta_client_manager.session_factory
        qd_client = qdrant_client_manager.client
        embedding_client = embedding_client_manager.embeddings
        es_client = es_client_manager.client

        async with (dw_session_factory() as dw_session,
                    meta_session_factory() as meta_session,
                    ):
            if es_client and qd_client and embedding_client:
                context = DataAgentContext(
                    writer=get_stream_writer(),
                    dw_mysql_repository=DWMySQLRepository(dw_session),
                    meta_mysql_repository=MetaMySQLRepository(meta_session),
                    embedding_client = embedding_client,
                    value_es_repository=ValueESRepository(es_client),
                    column_qdrant_repository=ColumnQdrantRepository(qd_client),
                    metric_qdrant_repository=MetricQdrantRepository(qd_client),
                )

            async for chunk in graph.astream(DataAgentState(query="华北地区销售总额"),context=context, stream_mode="custom"):
                print(chunk)


    asyncio.run(test_graph())
