from typing import TypedDict, List

from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo

# 指标信息封装实体
class MetricInfoStata(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]

class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]

# 表信息封装实体
class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]


class DataAgentState(TypedDict):
    query: str
    keywords: list[str]

    retrieved_columns: list[ColumnInfo]  # 召回的字段信息
    retrieved_values: list[ValueInfo]  # 召回的值信息
    retrieved_metrics: list[MetricInfo]  # 召回的指标信息

    metric_infos: list[MetricInfoStata] # 合并后的指标信息

    error: str