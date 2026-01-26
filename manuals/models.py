from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class SerialRange(BaseModel):
    from_serial: str = Field(alias="from")
    to_serial: str = Field(alias="to")

    model_config = {"extra": "ignore"}


class ManualFile(BaseModel):
    filename: str
    mime: str
    language: str
    type: str
    size: str
    hash: str
    download_url: str = Field(alias="link")

    model_config = {"extra": "ignore"}


class ManualDocument(BaseModel):
    type: str
    serials: List[SerialRange]
    files: List[ManualFile]

    model_config = {"extra": "ignore"}


class ManualsResponse(BaseModel):
    documents: List[ManualDocument]
    last_generated_at: datetime = Field(alias="lastGeneratedAt")
    time_to_generate: str = Field(alias="timeToGenerate")

    model_config = {"extra": "ignore"}


class UploadCandidate(BaseModel):
    document_type: str
    language: str
    filename: str
    download_url: str
    hash: str
