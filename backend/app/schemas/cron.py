from pydantic import BaseModel


class DailyDigestRequest(BaseModel):
    dryRun: bool | None = None


class OkResponse(BaseModel):
    ok: bool = True

