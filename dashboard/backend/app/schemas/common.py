from pydantic import BaseModel, Field


class ScenarioRequest(BaseModel):
    """A scenario: horizon plus optional per-channel budget overrides."""
    horizon: int = Field(30, description="Forecast horizon in days")
    budgets: dict[str, float] | None = Field(
        None, description="Per-channel period budgets; omitted channels use defaults")
