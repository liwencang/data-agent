from dataclasses import dataclass
from langgraph.types import StreamWriter


@dataclass
class DataAgentContext:
    writer: StreamWriter
