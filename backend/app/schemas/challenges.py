from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    prompt: str = Field(..., description="The user's prompt to be evaluated by the LLM")


class PromptResponse(BaseModel):
    response: str = Field(..., description="The model generated response")
    tokens_used: int = Field(..., description="The number of tokens consumed by the request")
    remaining_budget: int = Field(..., description="The remaining token budget for the session")
