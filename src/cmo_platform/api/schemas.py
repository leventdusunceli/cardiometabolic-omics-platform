"""Pydantic response models for the REST API"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    accession: str
    source: str
    title: str
    organism: str
    assay_type: str
    citation: str | None
    license: str | None
    ingestion_date: dt.datetime


class ExpressionValueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tissue: str
    condition: str
    gene_symbol: str
    normalized_value: float
    unit: str


class TaskSubmission(BaseModel):
    task_id: str
