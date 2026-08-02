from pathlib import Path

from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig
from app.core.log import logger


class MetaKnowledgeService:

    async def build(self, config_path: Path):
        context = OmegaConf.load(config_path)
        schema = OmegaConf.structured(MetaConfig)
        meta_config:MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))
        logger.info(meta_config.tables)
