"""GET /datasets — list ingested datasets with provenance."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from cmo_platform.api.dependencies import get_db
from cmo_platform.api.schemas import DatasetOut
from cmo_platform.db.models import Dataset

router = APIRouter(tags=["datasets"])


@router.get("/datasets", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db)) -> list[Dataset]:
    return db.query(Dataset).order_by(Dataset.accession).all()
