# 从 pathlib 库导入 Path 类，用于处理文件路径
import asyncio
from argparse import ArgumentParser
from pathlib import Path

from app.clients.elasticsearch_client_manager import ElasticsearchClientManager
from app.clients.embedding_client_manager import EmbeddedClientManager
from app.clients.mysql_client_manager import MysqlClientManager
from app.clients.qdrant_client_manager import QdrantClientManager
from app.conf.app_config import app_config
# 从 app.core.log 模块导入 logger 对象，用于日志记录
from app.core.log import logger
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService


# 定义 build 函数，接收一个 Path 类型的参数 config_path，表示配置文件路径
async def build(config_path: Path):
    # 打印日志，提示正在构建元知识
    logger.info("Building meta knowledge...")

    # 获取mysql session factory
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

    if qd_client is None :
        logger.error("No QDrant client found")
    if es_client is None :
        logger.error("No Elasticsearch client found")
    if qd_client and es_client and embedding_client:
        async with (dw_session_factory() as dw_session,
                    meta_session_factory() as meta_session):
            meta_knowledge_service = MetaKnowledgeService(
                DWMySQLRepository(dw_session),
                MetaMySQLRepository(meta_session),
                ColumnQdrantRepository(qd_client),
                embedding_client,
                ValueESRepository(es_client)
            )
            await meta_knowledge_service.build(config_path)
            await dw_client_manager.close()
            await meta_client_manager.close()
            await qd_client.close()
            await es_client.close()


# 当脚本被直接运行时执行以下代码
if __name__ == '__main__':
    # 创建一个命令行参数解析器对象
    parser = ArgumentParser()
    # 添加一个可选参数，支持短选项 -c 和长选项 --conf
    # 该选项用于接收配置文件的路径
    parser.add_argument('-c', '--conf')
    # 解析命令行传入的所有参数，并将结果存入 args 对象
    args = parser.parse_args()
    # 将命令行参数中获取的配置文件路径字符串，转换为 Path 对象
    config_path = Path(args.conf)
    # 调用 build 函数，传入解析后的配置文件路径
    asyncio.run(build(config_path))
