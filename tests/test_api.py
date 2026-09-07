import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from cmo_platform.api.dependencies import get_db
from cmo_platform.api.main import app
from cmo_platform.db.base import Base
from cmo_platform.db.models import (
    ConditionCategory,
    Dataset,
    DatasetSource,
    ExpressionUnit,
    ExpressionValue,
    Gene,
    Sample,
)


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    session = TestSession()
    dataset = Dataset(
        accession="gtex_v8_Liver",
        source=DatasetSource.GTEX,
        title="GTEx gtex_v8 median gene expression - Liver",
        assay_type="bulk RNA-seq",
        citation="GTEx Consortium, https://gtexportal.org",
    )
    sample = Sample(
        dataset=dataset,
        tissue="Liver",
        condition="population_baseline",
        condition_category=ConditionCategory.BASELINE,
    )
    gene = Gene(ensembl_gene_id="ENSG00000132693", symbol="CRP")
    session.add_all([dataset, sample, gene])
    session.flush()
    session.add(
        ExpressionValue(sample=sample, gene=gene, normalized_value=5683.19, unit=ExpressionUnit.TPM)
    )
    session.commit()
    session.close()

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_datasets(client):
    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["accession"] == "gtex_v8_Liver"


def test_get_gene_expression_found(client):
    response = client.get("/api/v1/tissues/Liver/genes/CRP/expression")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["normalized_value"] == pytest.approx(5683.19)


def test_get_gene_expression_not_found(client):
    response = client.get("/api/v1/tissues/Liver/genes/NOPE/expression")
    assert response.status_code == 404


def test_get_gene_expression_condition_filter_no_match(client):
    response = client.get("/api/v1/tissues/Liver/genes/CRP/expression?condition=disease")
    assert response.status_code == 404
