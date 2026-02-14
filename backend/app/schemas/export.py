from pydantic import BaseModel


class ExportLongshotRequest(BaseModel):
    contentId: str


class ExportLongshotResponse(BaseModel):
    url: str

