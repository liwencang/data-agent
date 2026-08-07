from langchain.chat_models import init_chat_model

from app.conf.app_config import app_config

llm = init_chat_model(
    model="deepseek-v4-flash",
    api_key=app_config.llm.api_key,
    temperature=0
)
