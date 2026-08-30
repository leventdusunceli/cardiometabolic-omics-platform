from __future__ import annotations

import datetime as dt
import enum
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cmo_platform.db.base import Base


class DatasetSource(enum.StrEnum):
    GTEX = "gtex"
    GEO = "geo"


class Sex(enum.StrEnum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"


class AnalysisType(enum.StrEnum):
    DIFFERENTIAL_EXPRESSION = "differential_expression"
    ENRICHMENT = "enrichment"
    CLUSTERING = "clustering"
    CROSSTALK = "crosstalk"


class AnalysisStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TriggeredVia(enum.StrEnum):
    API = "api"
    ETL = "etl"


class ExpressionUnit(enum.StrEnum):
    TPM = "tpm"
    DESEQ2_NORMALIZED = "deseq2_normalized"


def _str_enum(python_enum: type[enum.Enum]) -> Enum:
    """A SQLAlchemy Enum stored as VARCHAR + CHECK constraint (native_enum=False).

    Avoids Postgres native enum types, whose ALTER TYPE semantics make Alembic migrations
    (adding/removing a member) far more painful than adding a CHECK constraint value.
    """
    return Enum(python_enum, native_enum=False, validate_strings=True)


class Dataset(Base):
    """A single ingested data source (one GTEx tissue pull, or one GEO series)."""

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    accession: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    source: Mapped[DatasetSource] = mapped_column(_str_enum(DatasetSource))
    title: Mapped[str] = mapped_column(String(512))
    organism: Mapped[str] = mapped_column(String(128), default="Homo sapiens")
    assay_type: Mapped[str] = mapped_column(String(128))
    citation: Mapped[str | None] = mapped_column(String(1024))
    license: Mapped[str | None] = mapped_column(String(256))
    ingestion_date: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    checksum: Mapped[str | None] = mapped_column(String(128))

    samples: Mapped[list[Sample]] = relationship(back_populates="dataset")


class Sample(Base):
    """One biological sample (donor/tissue/condition) within a dataset."""

    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    tissue: Mapped[str] = mapped_column(String(128), index=True)
    condition: Mapped[str] = mapped_column(String(128), index=True)
    age_bracket: Mapped[str | None] = mapped_column(String(32))
    sex: Mapped[Sex | None] = mapped_column(_str_enum(Sex))
    bmi_category: Mapped[str | None] = mapped_column(String(32))
    # Heterogeneous per-dataset QC fields (library size, detected-gene count, etc.); kept as
    # JSON rather than fixed columns since GTEx and each GEO series report different metrics.
    qc_metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    dataset: Mapped[Dataset] = relationship(back_populates="samples")
    expression_values: Mapped[list[ExpressionValue]] = relationship(back_populates="sample")


class Gene(Base):
    """Reference gene table, loaded once from an Ensembl annotation."""

    __tablename__ = "genes"

    ensembl_gene_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    biotype: Mapped[str | None] = mapped_column(String(64))
    chromosome: Mapped[str | None] = mapped_column(String(16))


class ExpressionValue(Base):
    """A single gene's expression value in a single sample. Largest table in the schema."""

    __tablename__ = "expression_values"
    __table_args__ = (UniqueConstraint("sample_id", "gene_id", name="uq_expression_sample_gene"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("samples.id"), index=True)
    gene_id: Mapped[str] = mapped_column(ForeignKey("genes.ensembl_gene_id"), index=True)
    raw_count: Mapped[float | None] = mapped_column(Float)
    normalized_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[ExpressionUnit] = mapped_column(_str_enum(ExpressionUnit))

    sample: Mapped[Sample] = relationship(back_populates="expression_values")
    gene: Mapped[Gene] = relationship()


class AnalysisRun(Base):
    """Provenance record for one execution of an analysis task (DE, enrichment, clustering, ...).

    Every table below that stores derived results references its analysis_run_id, so any number
    served by the API can be traced back to the exact parameters and code path that produced it.
    """

    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[AnalysisType] = mapped_column(_str_enum(AnalysisType))
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[AnalysisStatus] = mapped_column(
        _str_enum(AnalysisStatus), default=AnalysisStatus.PENDING
    )
    submitted_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    triggered_via: Mapped[TriggeredVia] = mapped_column(_str_enum(TriggeredVia))
    result_reference: Mapped[str | None] = mapped_column(String(512))

    de_results: Mapped[list[DifferentialExpressionResult]] = relationship(
        back_populates="analysis_run"
    )
    crosstalk_modules: Mapped[list[CrosstalkModule]] = relationship(back_populates="analysis_run")


class DifferentialExpressionResult(Base):
    """One gene's DE statistics from one analysis run, for one tissue."""

    __tablename__ = "differential_expression_results"
    __table_args__ = (
        UniqueConstraint(
            "analysis_run_id", "gene_id", "tissue", name="uq_de_result_run_gene_tissue"
        ),
        Index("ix_de_result_tissue_padj", "tissue", "padj"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    gene_id: Mapped[str] = mapped_column(ForeignKey("genes.ensembl_gene_id"), index=True)
    tissue: Mapped[str] = mapped_column(String(128))
    log2_fold_change: Mapped[float] = mapped_column(Float)
    pvalue: Mapped[float] = mapped_column(Float)
    padj: Mapped[float] = mapped_column(Float)

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="de_results")
    gene: Mapped[Gene] = relationship()


class CrosstalkModule(Base):
    """A cross-tissue gene/pathway module discovered by the crosstalk-discovery analysis."""

    __tablename__ = "crosstalk_modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(String(1024))

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="crosstalk_modules")
    genes: Mapped[list[CrosstalkModuleGene]] = relationship(back_populates="module")


class CrosstalkModuleGene(Base):
    """One (module, gene, tissue) membership row: which tissue a module's gene recurs in."""

    __tablename__ = "crosstalk_module_genes"
    __table_args__ = (
        UniqueConstraint("module_id", "gene_id", "tissue", name="uq_module_gene_tissue"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("crosstalk_modules.id"), index=True)
    gene_id: Mapped[str] = mapped_column(ForeignKey("genes.ensembl_gene_id"), index=True)
    tissue: Mapped[str] = mapped_column(String(128))

    module: Mapped[CrosstalkModule] = relationship(back_populates="genes")
    gene: Mapped[Gene] = relationship()
