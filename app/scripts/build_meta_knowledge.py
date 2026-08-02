# 从 pathlib 库导入 Path 类，用于处理文件路径
import asyncio
from argparse import ArgumentParser
from pathlib import Path
# 从 app.core.log 模块导入 logger 对象，用于日志记录
from app.core.log import logger
from app.services.meta_knowledge_service import MetaKnowledgeService


# 定义 build 函数，接收一个 Path 类型的参数 config_path，表示配置文件路径
async def build(config_path: Path):
    # 打印日志，提示正在构建元知识
    logger.info("Building meta knowledge...")
    meta_knowledge_service = MetaKnowledgeService()
    await meta_knowledge_service.build(config_path)

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