from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.column_info import ColumnInfo
from app.entities.table_info import TableInfo
from app.mappers.column_info_mapper import ColumnInfoMapper
from app.mappers.table_info_mapper import TableInfoMapper


class MetaMySQLRepository:
    """跟MySQL数据库（元数据库）交互持久层 必须通过Session对象进行CURD"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_table_infos(self, table_infos: List[TableInfo]):
        table_models = [TableInfoMapper.to_model(table_info) for table_info in table_infos]
        self.session.add_all(table_models)

    async def save_column_infos(self, column_infos: List[ColumnInfo]):
        column_models = [ColumnInfoMapper.to_model(column_info) for column_info in column_infos]
        self.session.add_all(column_models)

