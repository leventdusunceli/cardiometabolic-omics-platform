# Cardiometabolic Crosstalk Omics Platform

A multi-tissue transcriptomics data platform exploring shared biology between type 2 diabetes
(T2D) and cardiovascular risk, inspired by public research on cardiometabolic disease.

**This is a work-in-progress README** describing the project's aims, its design, and its current
state. A quickstart and example API calls will land once the core pipeline runs end to end in
Docker.

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
2. Curates that data into a documented, queryable database. Every data load is logged with a
   fingerprint of the data, so changes to a dataset over time stay visible.
3. Runs differential expression (DE) and pathway enrichment per tissue.
4. Looks for which pathways recur across tissues.
5. Serves the data and results through a REST API. Users can also request new analyses on the
   hosted datasets (for example, a different pair of patient groups, or a different gene-set
   library). These run as background jobs, and the API reports their progress.

Every result states its sample size and is framed as portfolio-scale and exploratory, not a
validated clinical finding. Public GEO datasets in this space are genuinely small, and that
limitation is disclosed plainly, not smoothed over.

## Tech stack

- **Language**: Python (typed, `mypy --strict`)
- **Database**: PostgreSQL, via SQLAlchemy (2.x) and Alembic migrations
- **API**: FastAPI, with auto-generated OpenAPI/Swagger docs
- **Orchestration**: Prefect, for the ETL pipeline (one command runs everything)
- **Background jobs**: a job list stored in Postgres (the `analysis_runs` table), worked through
  by a small job runner process
- **Bioinformatics / ML**: `pydeseq2` (differential expression), `gseapy` (pathway enrichment),
  `scikit-learn` (clustering), `pandas`
- **Data sources**: GTEx Portal REST API, NCBI GEO / E-utilities, HGNC (gene symbols), public
  gene-set libraries (for example MSigDB Hallmark)
- **Infra & tooling**: Docker Compose, `uv` (dependency management), `pytest`, `ruff`, GitHub
  Actions CI

## Architecture

```text
Public sources (GTEx API, GEO, HGNC, gene-set libraries)
        |
        v
  Prefect pipeline (one command)
  fetch -> QC -> normalize -> load -> DE -> enrichment
        |                                  |
        | logs every load                  | runs analyses directly
        v                                  v
  +------------------------------------------------------+
  |  Postgres                                            |
  |  datasets, samples, genes, expression_values         |
  |  ingestion_runs   (history of every data load)       |
  |  analysis_runs    (job list + provenance record)     |
  |  DE / enrichment results (linked to analysis_runs)   |
  +------------------------------------------------------+
        ^                                  ^
        | reads results, adds              | takes the next pending job,
        | "pending" analysis requests      | writes progress and results
        |                                  |
  REST API (FastAPI)                 Job runner
        ^
        |
  Users: query results, submit analyses, check progress
```

Analyses are started in two ways, and both run the same analysis code:

- **The pipeline** runs the official analysis for each tissue as part of ingestion.
- **API users** submit a request (`POST /api/v1/analyses`). The API checks it, stores it as a
  `pending` row in `analysis_runs`, and returns a job id right away. The job runner picks it up,
  runs it, and updates its progress. The user checks the job's status
  (`GET /api/v1/analyses/{id}`) until it is done, then reads the results.

User-requested analyses run only on the datasets this platform hosts. Uploading your own data is
deliberately not supported. It would need a strict upload format, storage, and checks that
uploads contain no identifiable patient data, which is out of scope for a platform built on
public, de-identified data.

## Traceability

Every number the API returns can be traced back to where it came from:

```text
a DE or enrichment result
  -> the analysis run that produced it: settings, code version (git commit),
     package versions, exact samples in each group
  -> the data load it read: data fingerprint, samples removed by QC and why
  -> the source dataset: accession and citation
```

Enrichment results also link to the DE run they were built from, and record the exact gene-set
library file used.

## API overview

| Endpoint | Purpose | Status |
| --- | --- | --- |
| `GET /api/v1/datasets` | Ingested datasets with citation and provenance | Live |
| `GET /api/v1/tissues/{tissue}/genes/{gene}/expression` | Expression of one gene in one tissue | Live (gene by symbol or Ensembl ID) |
| `GET /api/v1/tissues/{tissue}/conditions` | Which groups exist and how many samples each | Planned |
| `POST /api/v1/analyses` | Submit a DE or enrichment analysis on hosted data | Planned |
| `GET /api/v1/analyses` | List analysis runs, filterable by type, tissue, status | Planned |
| `GET /api/v1/analyses/{id}` | Status, progress, settings and provenance of one run | Planned |
| `GET /api/v1/analyses/{id}/de-results` | DE results of one run, filterable and paged | Planned |
| `GET /api/v1/tissues/{tissue}/de-results` | The official DE result for a tissue | Planned |
| `GET /api/v1/genes/{gene}/de-results` | One gene's DE result across all tissues | Planned |
| `GET /api/v1/analyses/{id}/enrichment-results` | Enrichment results of one run | Planned |
| `GET /api/v1/tissues/{tissue}/enrichment-results` | The official enrichment result for a tissue | Planned |
| `GET /api/v1/crosstalk/modules` | Pathways and genes recurring across tissues | Planned |
| `GET /api/v1/health` | Database reachable, job list state | Planned |

## Current status

- **Done:** scaffolding, CI, database schema; GTEx baseline for all four tissues; first API
  endpoints; liver GEO dataset loaded and analyzed with `pydeseq2`; official gene names
  (HGNC) for the `genes` table.
- **In progress:** moving to the Postgres job list. RabbitMQ and Celery are removed; the liver
  pipeline (download, QC, normalization, load, `pydeseq2`) now runs end to end as one Prefect flow.

- **Next:** job runner and analysis endpoints, the data load history (`ingestion_runs`), pathway
  enrichment, the other three GEO tissues, cross-tissue crosstalk analysis.

See `DATA_SOURCES.md` for the exact datasets used and their provenance.
