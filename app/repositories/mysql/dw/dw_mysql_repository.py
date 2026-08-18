import datetime
from decimal import Decimal

from sqlalchemy import text, Result
from sqlalchemy.ext.asyncio import AsyncSession


class DWMySQLRepository:
    """跟MySQL数据库（数仓数据库）交互持久层 必须通过Session对象进行CURD"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_db_version(self) -> str:
        """查询数据库版本"""
        sql = "SELECT VERSION()"
        result: Result = await self.session.execute(text(sql))
        return result.scalar_one()

    def get_db_dialect(self) -> str:
        """获取数据库方言类型（如 mysql）"""
        return self.session.bind.dialect.name

    async def validate_sql(self, sql: str) -> Result:
        """使用EXPLAIN校验SQL语句合法性"""
        explain_sql = f"EXPLAIN {sql}"
        result: Result = await self.session.execute(text(explain_sql))
        return result

    async def execute_sql(self, sql: str) -> list[dict]:
        """执行SQL查询，返回字段名到值的字典列表（JSON可序列化）"""
        result: Result = await self.session.execute(text(sql))
        rows = []
        for row in result.mappings().all():
            row_dict = {}
            for key, value in row.items():
                row_dict[key] = self._to_json_serializable(value)
            rows.append(row_dict)
        return rows

    @staticmethod
    def _to_json_serializable(value):
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
            return value.isoformat()
        return value



    # async def get_column_values_by_table_id(self, table_id: str, column_name: str, limit: int = 10) -> list[str]:
    #     """查询指定个数某张表某个字段取值"""
    #     sql = f"SELECT distinct {column_name} from {table_id} limit {limit}"
    #     result: Result = await self.session.execute(text(sql))
    #     # 结果：一列多行
    #     return result.scalars().fetchall()

    async def get_column_type_by_table_name(self, table_name):
        """根据表面查询表中所有字段的类型，返回一个字典"""
        sql = f"show columns from {table_name}"
        result: Result = await self.session.execute(text(sql))
        return {row.Field: row.Type for row in result.fetchall()}

    async def get_column_value_by_column_name(self, column_name, table_name):
        sql = f"SELECT DISTINCT {column_name}  FROM {table_name} limit 3"
        result: Result = await self.session.execute(text(sql))
        return result.scalars().fetchall()

    async def get_column_values_by_table_id(self, table_id: str, column_name: str, limit: int = 10):
        """查询指定个数某张表某个字段取值"""
        sql = f"SELECT distinct {column_name} from {table_id} limit {limit}"
        result: Result = await self.session.execute(text(sql))
        # 结果：一列多行
        return result.scalars().fetchall()