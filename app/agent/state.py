from typing import TypedDict


class DataAgentState(TypedDict):
    query: str
    keywords: str
    error: str