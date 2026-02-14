from pydantic import BaseModel


class PlanStatsResponse(BaseModel):
    secsToday: int
    streak: int

