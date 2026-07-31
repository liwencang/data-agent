from typing import Optional
from pydantic import SecretStr
from app.conf.app_config import EmbeddingConfig, app_config
from langchain_openai import OpenAIEmbeddings


class EmbeddedClientManager:
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.embeddings: Optional[OpenAIEmbeddings] = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}/v1"

    def init(self):
        self.embeddings = OpenAIEmbeddings(
            model=self.config.model,
            base_url=self._get_url(),
            api_key=SecretStr("unused"),
            check_embedding_ctx_length=False,  # send raw text; TEI tokenizes server-side
        )

if __name__ == "__main__":
    client = EmbeddedClientManager(app_config.embedding)
    client.init()
    embeddings = client.embeddings
    query = embeddings.embed_query("你好")
    print(query)
    print(len(query))


