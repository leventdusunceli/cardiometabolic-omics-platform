import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from cmo_platform.db.base import Base
from cmo_platform.db.models import (
    AnalysisRun,
    AnalysisType,
    ConditionCategory,
    CrosstalkModule,
    CrosstalkModuleGene,
    Dataset,
    DatasetSource,
    DifferentialExpressionResult,
    ExpressionUnit,
    ExpressionValue,
    Gene,
    Sample,
    TriggeredVia,
)


@pytest.fixture
def session() -> Session:
    # SQLite in-memory: enough to verify ORM wiring/constraints without a live Postgres.
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


def test_dataset_sample_gene_expression_round_trip(session: Session) -> None:
    dataset = Dataset(
        accession="GTEX-LIVER",
        source=DatasetSource.GTEX,
        title="GTEx Liver bulk RNA-seq",
        assay_type="bulk RNA-seq",
    )
    gene = Gene(ensembl_gene_id="ENSG00000141510", symbol="TP53")
    sample = Sample(
        dataset=dataset,
        tissue="Liver",
        condition="control",
        condition_category=ConditionCategory.CONTROL,
    )
    expression = ExpressionValue(
        sample=sample, gene=gene, normalized_value=12.3, unit=ExpressionUnit.TPM
    )
    session.add_all([dataset, gene, sample, expression])
    session.commit()

    stored = session.query(ExpressionValue).one()
    assert stored.sample.tissue == "Liver"
    assert stored.gene.symbol == "TP53"
    assert stored.normalized_value == pytest.approx(12.3)


def test_expression_value_unique_per_sample_gene(session: Session) -> None:
    dataset = Dataset(
        accession="GTEX-LIVER-2",
        source=DatasetSource.GTEX,
        title="GTEx Liver bulk RNA-seq",
        assay_type="bulk RNA-seq",
    )
    gene = Gene(ensembl_gene_id="ENSG00000141510", symbol="TP53")
    sample = Sample(
        dataset=dataset,
        tissue="Liver",
        condition="control",
        condition_category=ConditionCategory.CONTROL,
    )
    session.add_all(
        [
            dataset,
            gene,
            sample,
            ExpressionValue(
                sample=sample, gene=gene, normalized_value=1.0, unit=ExpressionUnit.TPM
            ),
        ]
    )
    session.commit()

    session.add(
        ExpressionValue(sample=sample, gene=gene, normalized_value=2.0, unit=ExpressionUnit.TPM)
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_derived_results_trace_back_to_analysis_run(session: Session) -> None:
    gene = Gene(ensembl_gene_id="ENSG00000141510", symbol="TP53")
    run = AnalysisRun(
        type=AnalysisType.DIFFERENTIAL_EXPRESSION,
        parameters={"tissue": "Liver"},
        triggered_via=TriggeredVia.API,
    )
    de_result = DifferentialExpressionResult(
        analysis_run=run,
        gene=gene,
        tissue="Liver",
        log2_fold_change=1.5,
        pvalue=0.001,
        padj=0.01,
    )
    module = CrosstalkModule(analysis_run=run, name="inflammation-module")
    module_gene = CrosstalkModuleGene(module=module, gene=gene, tissue="Liver")
    session.add_all([gene, run, de_result, module, module_gene])
    session.commit()

    stored_run = session.query(AnalysisRun).one()
    assert stored_run.de_results[0].padj == pytest.approx(0.01)
    assert stored_run.crosstalk_modules[0].genes[0].tissue == "Liver"
