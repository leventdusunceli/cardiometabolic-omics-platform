"""GET /tissues/{tissue}/genes/{gene}/expression."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cmo_platform.api.dependencies import get_db
from cmo_platform.api.schemas import ExpressionValueOut
from cmo_platform.db.models import ExpressionValue, Gene, Sample

router = APIRouter(tags=["expression"])


@router.get(
    "/tissues/{tissue}/genes/{gene}/expression",
    response_model=list[ExpressionValueOut],
)
def get_gene_expression(
    tissue: str,
    gene: str,
    condition: str | None = None,
    db: Session = Depends(get_db),
) -> list[ExpressionValueOut]:
    query = (
        db.query(ExpressionValue, Sample, Gene)
        .join(Sample, ExpressionValue.sample_id == Sample.id)
        .join(Gene, ExpressionValue.gene_id == Gene.ensembl_gene_id)
        .filter(Sample.tissue == tissue, Gene.symbol == gene)
    )
    if condition is not None:
        query = query.filter(Sample.condition == condition)

    rows = query.all()
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No expression data for gene={gene!r} in tissue={tissue!r}",
        )

    return [
        ExpressionValueOut(
            tissue=sample.tissue,
            condition=sample.condition,
            gene_symbol=gene_row.symbol,
            normalized_value=ev.normalized_value,
            unit=ev.unit,
        )
        for ev, sample, gene_row in rows
    ]
