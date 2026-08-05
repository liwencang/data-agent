import json
import uuid
from pathlib import Path
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from omegaconf import OmegaConf
from app.conf.meta_config import MetaConfig
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:

    def __init__(
            self,
            dw_mysql_repository: DWMySQLRepository,
            meta_mysql_repository: MetaMySQLRepository,
            column_qdrant_repository: ColumnQdrantRepository,
            metric_qdrant_repository: MetricQdrantRepository,
            embedding_client: OpenAIEmbeddings
    ):
        self.dw_mysql_repository = dw_mysql_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.embedding_client = embedding_client
        self.metric_qdrant_repository = metric_qdrant_repository

    async def build(self, config_path: Path):
        # 1. 通过OmegaConf读取元数据配置文件 得到需要同步表格信息、指标信息
        context = OmegaConf.load(config_path)
        schema = OmegaConf.structured(MetaConfig)
        meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))
        # 2. 处理表格信息
        # 2.1 表、列信息存储到 mysql
        # if meta_config.tables:
        #     column_infos: List[ColumnInfo] = await self._save_table_info_to_meta_db(meta_config)
        #     logger.info(f"批量保存表信息成功")
        #     # 2.2 存储字段信息到qdrant
        #     await self._save_column_info_to_qdrant(column_infos)
        #     logger.info(f"为字段信息建立向量索引成功")
        #     # 2.3 存储字段信息到es
        #     await self._save_value_info_to_es(meta_config, column_infos)
        #     logger.info(f"为字段取值建立全文索引成功 ")
        if meta_config.metrics:
            # 3.1 将指标信息存入到meta元数据库
            metric_infos: list[MetricInfo] = await self._save_metric_info_to_meta_db(meta_config)
            print(metric_infos)
            logger.info("指标信息存入到meta元数据库成功")

            #  3.2 为指标信息建立向量索引 存入 Qdrant
            await self._save_metric_info_to_qdrant(metric_infos)
            logger.info("为指标信息建立向量索引成功")

    # 保存表的信息到meta_db
    async def _save_table_info_to_meta_db(self, meta_config: MetaConfig) -> List[ColumnInfo]:
        # 表信息为空直接结束
        if meta_config.tables is None:
            logger.info("meta_config.tables is None")
            return []

        table_infos: List[TableInfo] = []
        column_infos: List[ColumnInfo] = []
        # 遍历表信息
        for table in meta_config.tables:
            # 获取表信息
            table_info = TableInfo(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description,
            )
            table_infos.append(table_info)  # 追加到列表

            # 先获取column的type(字典)
            column_type_dict: Dict[str, str] = await self.dw_mysql_repository.get_column_type_by_table_name(table.name)

            # 获取table里的column信息
            for column in table.columns:
                # 获取列示例
                examples: List[Any] = await self.dw_mysql_repository.get_column_value_by_column_name(column.name,
                                                                                                     table.name)
                column_info = ColumnInfo(
                    id=f"{table.name}.{column.name}",
                    table_id=table.name,
                    role=column.role,
                    name=column.name,
                    alias=column.alias,
                    description=column.description,
                    type=column_type_dict[column.name],
                    examples=examples,
                )
                column_infos.append(column_info)  # 追加到列表

        # 批量保存表、列信息打meta_db中
        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_table_infos(table_infos)
            await self.meta_mysql_repository.save_column_infos(column_infos)
        return column_infos

    async def _save_column_info_to_qdrant(self, column_infos: List[ColumnInfo]):
        # 判断数据库是否存在，不存在则创建
        await self.column_qdrant_repository.ensure_collection()

        # 将column_infos保存到qdrant中
        # 定义未embedding的points
        points = []
        for column_info in column_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.name,
                "payload": column_info
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.description,
                "payload": column_info
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.alias,
                "payload": column_info
            })
        embeddings = []
        batch_size = 10
        embeddings_text = [point["embedding_text"] for point in points]
        for i in range(0, len(points), batch_size):
            batch_embedding_text = embeddings_text[i:i + batch_size]
            # 将里面的列表转为str
            for i in range(0, len(batch_embedding_text)):
                if not isinstance(batch_embedding_text[i], str):
                    batch_embedding_text[i] = json.dumps(batch_embedding_text[i])

            batch_embeddings = await self.embedding_client.aembed_documents(batch_embedding_text)
            embeddings.extend(batch_embeddings)

        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.column_qdrant_repository.upsert(ids, embeddings, payloads, 10)

    async def _save_value_info_to_es(self, meta_config: MetaConfig, column_infos: list[ColumnInfo]):
        # 创建索引库
        await self.value_es_repository.ensure_index()
        """封装es持久层需要 字段取值ValueInfo列表,调用es持久层批量保存"""
        # 1.初始化字段值列表
        value_infos: list[ValueInfo] = []

        # 2.从人工配置元信息得到需要同步到ES字段列表
        if meta_config.tables:
            colum2es = [column.name for table in meta_config.tables for column in table.columns if column.sync == True]
        else:
            colum2es = []
            logger.warning("meta_config.tables is None")

        # 3.遍历字段列表，查询出字段枚举值构建ValueInfo对象
        for column_info in column_infos:
            if column_info.name in colum2es:
                # 根据表ID和字段名称查询字段取值
                # 说明该字段取值需要存入ES，需要构建ValueInfo对象
                values = await self.dw_mysql_repository.get_column_values_by_table_id(column_info.table_id,
                                                                                      column_info.name, limit=100000)
                for value in values:
                    value_info = ValueInfo(
                        id=f"{column_info.id}.{value}",
                        value=value,
                        column_id=column_info.id
                    )
                    value_infos.append(value_info)
        # 4.调用es持久层批量保存文档
        await self.value_es_repository.upsert(value_infos)

    async def _save_metric_info_to_meta_db(self, meta_config):

        # 组装List[dataclass]
        metric_infos: list[MetricInfo] = []
        column_metrics: list[ColumnMetric] = []
        for item in meta_config.metrics:
            metric_infos.append(MetricInfo(
                id=item.name,
                name=item.name,
                description=item.description,
                relevant_columns=item.relevant_columns,
                alias=item.alias,
            ))
            for relevant_column in item.relevant_columns:
                column_metric = ColumnMetric(
                    metric_id=item.name,
                    column_id=relevant_column
                )
                column_metrics.append(column_metric)

        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_metric_info_to_meta_db(metric_infos)
            await self.meta_mysql_repository.save_column_metric_info_to_meta_db(column_metrics)
        return metric_infos

    async def _save_metric_info_to_qdrant(self, metric_infos):
        # 判断数据库是否存在，不存在则创建
        await self.metric_qdrant_repository.ensure_collection()

        # 将column_infos保存到qdrant中
        # 定义未embedding的points
        points = []
        for metric_info in metric_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.name,
                "payload": metric_info
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.description,
                "payload": metric_info
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.alias,
                "payload": metric_info
            })
        embeddings = []
        batch_size = 10
        embeddings_text = [point["embedding_text"] for point in points]
        for i in range(0, len(points), batch_size):
            batch_embedding_text = embeddings_text[i:i + batch_size]
            # 将里面的列表转为str
            for i in range(0, len(batch_embedding_text)):
                if not isinstance(batch_embedding_text[i], str):
                    batch_embedding_text[i] = json.dumps(batch_embedding_text[i])

            batch_embeddings = await self.embedding_client.aembed_documents(batch_embedding_text)
            embeddings.extend(batch_embeddings)

        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.metric_qdrant_repository.upsert(ids, embeddings, payloads, 10)
