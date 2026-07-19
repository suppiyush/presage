from pydantic import BaseModel, Field


class NarrativeRequest(BaseModel):
    horizon: int = Field(30, description="Forecast horizon in days")
    budgets: dict[str, float] | None = None


class NarrativeResponse(BaseModel):
    text: str
    provider: str
    generated_at: str
