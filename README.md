# Cardiometabolic Crosstalk Omics Platform

A multi-tissue transcriptomics data platform exploring shared biology between type 2 diabetes
(T2D) and cardiovascular risk, inspired by public research on cardiometabolic disease.

**This is a preliminary, work-in-progress README** describing the project's aims and current
state. A full pitch, quickstart, and example API calls will land once the core pipeline is
working end to end.

## The biological problem

T2D and cardiovascular disease are usually taught as separate conditions, linked mainly through
shared risk factors like high blood sugar damaging blood vessels. A more current view is
different. Several peripheral organs actively generate the systemic state that puts the heart and
blood vessels at risk. The heart is not just a downstream victim of high glucose.

Four tissues do most of this work, each with real evidence behind it:

- **Liver**: fat accumulation and inflammation drive a harmful circulating lipid profile (Duell
  et al., 2022, *Arterioscler Thromb Vasc Biol*).
- **Gut**: increased intestinal permeability raises circulating bacterial endotoxin, which alone
  can drive insulin resistance (Cani et al., 2007, *Diabetes*).
- **Adipose tissue**: under obesity, fat tissue shifts toward a pro-inflammatory, immune-cell-rich
  state linked to insulin resistance (Hotamisligil et al., 1993, *Science*; Weisberg et al., 2003,
  *J Clin Invest*).
- **Bone marrow / hematopoietic compartment**: blood-forming stem cells respond to systemic
  inflammation, and this axis is tied directly to cardiovascular risk in humans (Jaiswal et al.,
  2017, *N Engl J Med*).

This project's actual claim is narrower than "these organs cause heart disease." If the four
organs are mechanistically linked as the literature describes, their disease-associated gene
expression should show recurring, overlapping pathway disturbances. This should happen more than
expected from independent, tissue-specific noise. That overlap is the "crosstalk" in the project
name. It is a hypothesis-generating, exploratory analysis, not a mechanistic proof.

**Note on scope**: whole blood is used as a proxy for the bone marrow / hematopoietic
compartment. Blood is the direct downstream output of that compartment, and it is what the
clinical evidence above was actually measured from. This is stated explicitly wherever it's used,
not treated as a claim of tissue equivalence.

## What the platform does

1. Ingests public bulk RNA-seq data for the four tissues, from GTEx (baseline, architecture
   validation) and NCBI GEO (disease vs. healthy, the real analysis substrate).
2. Curates that data into a documented, queryable database with full analysis provenance.
3. Runs differential expression and pathway enrichment per tissue.
4. Looks for which pathways recur across tissues.
5. Serves the data and results through a REST API, with long analyses run as background jobs.

Every result states its sample size and is framed as portfolio-scale and exploratory, not a
validated clinical finding. Public GEO datasets in this space are genuinely small, and that
limitation is disclosed plainly, not smoothed over.

## Tech stack

- **Language**: Python (typed, `mypy --strict`)
- **Database**: PostgreSQL, via SQLAlchemy (2.x) and Alembic migrations
- **API**: FastAPI, with auto-generated OpenAPI/Swagger docs
- **Orchestration**: Prefect, for ETL workflows
- **Async jobs**: RabbitMQ + Celery
- **Bioinformatics / ML**: `pydeseq2` (differential expression), `gseapy` (pathway enrichment),
  `scikit-learn` (clustering), `pandas`
- **Data sources**: GTEx Portal REST API, NCBI GEO / E-utilities
- **Infra & tooling**: Docker Compose, `uv` (dependency management), `pytest`, `ruff`, GitHub
  Actions CI

## Architecture

```text
Public sources (GTEx REST API, GEO)
        |
        v
  ETL orchestration (Prefect flows)
        |
        v
  Postgres database  <----->  REST API (FastAPI)
        |                          |
        v                          v
  Message queue (RabbitMQ)   OpenAPI docs / results
        |
        v
  Analysis workers (Celery: pydeseq2, gseapy, scikit-learn)
```

Everything runs locally via Docker Compose. The schema tracks datasets, samples, genes,
expression values, and analysis runs as linked records, so every result is traceable back to the
data and parameters that produced it.

## Current status

**Done:**

- Repo scaffolding, CI, Postgres schema with migrations.
- GTEx baseline ingested for all four tissues.
- REST API live (`GET /datasets`, gene-expression queries).
- RabbitMQ + Celery wired and proven with a real async job.

**In progress:**

- GEO disease-dataset ingestion. All four datasets validated (`DATA_SOURCES.md`).
- GEO parsing client built.
- Liver case/control mapping built.
- Next: QC, normalization, loading, and the first real `pydeseq2` run.

**Not started:**

- Pathway enrichment, cross-tissue crosstalk analysis, subtype discovery, narrative notebook.

See `DATA_SOURCES.md` for the exact datasets used and their provenance.
