from pydantic import BaseModel


class ChatAgentRequest(BaseModel):
    query: str