from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, MetricInfoStata, TableInfoState, ColumnInfoState
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo


async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 流写入器
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "合并召回信息", "status": "running"})
    try:
        meta_mysql_repository = runtime.context.meta_mysql_repository

        retrieved_columns = state["retrieved_columns"]
        retrieved_values = state["retrieved_values"]
        retrieved_metrics: list[MetricInfo] = state["retrieved_metrics"]

        # 1. 合并三路信息的字段信息
        # 1.1 获取retrieved_columns的字段信息
        # 列表推导式声明字段信息dict
        retrieved_columns_map: dict[str, ColumnInfo] = {column_info.id: column_info for column_info in
                                                        retrieved_columns}

        # 1.2 获取retrieved_metrics的字段信息
        for retrieved_metric in retrieved_metrics:
            for metric_column_id in retrieved_metric.relevant_columns:
                if metric_column_id not in retrieved_columns_map:
                    column_info: ColumnInfo = await meta_mysql_repository.get_column_info_by_id(metric_column_id)
                    retrieved_columns_map[metric_column_id] = column_info

        # 1.3 获取retrieved_values的字段信息
        for retrieved_value in retrieved_values:
            key = retrieved_value.column_id
            if key not in retrieved_columns_map:
                column_info: ColumnInfo = await meta_mysql_repository.get_column_info_by_id(key)
                retrieved_columns_map[key] = column_info
            # 1.3.1 把字段信息字典里的examples里没有取到的值放进去
            if retrieved_value.value not in retrieved_columns_map[key].examples:
                retrieved_columns_map[key].examples.append(retrieved_value.value)

        # 2 按table_id分组 得到表跟字段列表映射字典 {"table_id1":[{ColumnInfo1},{ColumnInfo1}],"table_id2":[]}
        table_id_to_columns_map: dict[str, list[ColumnInfo]] = {}
        # 2.1 遍历retrieved_columns_map 整合里面的table->list[ColumnInfo]
        for column_info in retrieved_columns_map.values():
            table_id = column_info.table_id
            # 如果table_id没有在table_id_to_columns_map中
            if table_id not in table_id_to_columns_map:
                table_id_to_columns_map[table_id] = []
            table_id_to_columns_map[table_id].append(column_info)

        # 2.2 对相关表显式增加主外键字段信息 为上面字典中字段列表中补充主外键字段信息
        for table_id in table_id_to_columns_map:
            # 获取现有字段的id，用于后面判断
            column_ids: list[str] = [column.id for column in table_id_to_columns_map[table_id]]
            # 获取主、外键属性的字段
            key_column_infos = await meta_mysql_repository.get_key_column_by_table_id(table_id)
            for key_column_info in key_column_infos:
                # 主外键字段不在table_id_to_columns_map中则加入
                if key_column_info.id not in column_ids:
                    table_id_to_columns_map[table_id].append(key_column_info)

        # 3 将table_id ---->list[ColumnInfo]   封装state中表信息列表：list[TableInfoState]
        table_infos: list[TableInfoState] = []
        for table_id, column_infos in table_id_to_columns_map.items():
            table_info = await meta_mysql_repository.get_table_info_by_table_id(table_id)
            table_info_state = TableInfoState(
                name=table_info.name,
                role=table_info.role,
                description=table_info.description,
                # 4.2 处理表中字段：将列表list[ColumnInfo]转为list[ColumnInfoState]
                columns=[ColumnInfoState(
                    name=column_info.name,
                    type=column_info.type,
                    role=column_info.role,
                    examples=column_info.examples,
                    description=column_info.description,
                    alias=column_info.alias
                ) for column_info in column_infos]
            )
            table_infos.append(table_info_state)
        logger.info(f"合并信息，表列表：{[table["name"] for table in table_infos]}")
        logger.info(f"合并信息，字段列表：{[column["name"] for table in table_infos for column in table["columns"]]}")

        # 4. 封装state中指标信息列表：list[MetricInfoState]
        retrieved_metrics = state['retrieved_metrics']
        retrieved_infos: list[MetricInfoStata] = []
        if retrieved_metrics:
            for retrieved_metric in retrieved_metrics:
                retrieved_infos.append(
                    MetricInfoStata(
                        name=retrieved_metric.name,
                        description=retrieved_metric.description,
                        relevant_columns=retrieved_metric.relevant_columns,
                        alias=retrieved_metric.alias
                    )
                )
        writer({"type": "progress", "step": "合并召回信息", "status": "success"})
        logger.info(f"合并信息，指标列表：{[metric_info["name"] for metric_info in retrieved_infos]}")
        return {"metric_infos": retrieved_infos, "table_infos": table_infos}
    except Exception as e:
        writer({"type": "progress", "step": "合并召回信息", "status": "error"})
        logger.error(f"合并召回信息失败, 错误信息: {str(e)}")
        raise
