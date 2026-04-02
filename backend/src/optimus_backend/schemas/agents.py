from pydantic import BaseModel


class AgentCatalogItem(BaseModel):
    key: str
    title: str
    responsibilities: list[str]
