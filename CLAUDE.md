# Project: Cardiometabolic Crosstalk Omics Platform

## 0. Read this first

You (Claude Code) are building a portfolio project for a bioinformatician (Master's in Life
Science Informatics, prior automated-pipeline experience at Fraunhofer SCAI, strong Python/SQL/
Linux/Docker/Git background, basic R). The goal of this project is to credibly demonstrate, in one
coherent codebase, the exact skill combination that recurs in current bioinformatics/data-science
job postings at German university hospitals and research consortia: a Python "data science stack"
(REST APIs, databases, message queuing systems, ETL workflows) applied to real genomic/
transcriptomic data, with enough biological depth to be convincing to a domain-expert reviewer,
not just a software engineer.

This is a portfolio piece, not a production clinical system. Prioritize correctness, reproducibility,
and clear documentation over scale. Every design decision below should be defensible in an
interview: be ready to explain *why* a component exists, not just *that* it exists.

Act as a senior bioinformatics/data engineering expert who also has applied ML experience.
Apply the standards a strict academic PI and a data-platform engineering lead would both hold
you to: statistical rigor (multiple testing correction, documented assumptions, no p-hacking),
reproducibility (pinned dependencies, containerization, seeded randomness), and software
engineering hygiene (tests, typed code, CI, structured logging, meaningful commit history).

## 1. Context and inspiration (do not copy any text below into the codebase verbatim)

This project is inspired by two real, current job postings the developer is targeting, used here
only to shape the *type* of system to build, not to be referenced, quoted, or named in any
committed file, README, or commit message:

- A "Wissenschaftliche/r Mitarbeiter/in / Data Steward" role at a university hospital's Core Unit
  Bioinformatik, supporting a large interdisciplinary research consortium studying why type 2
  diabetes patients remain at elevated cardiovascular risk. That consortium studies four organs
  it calls "promoter organs" (gut, adipose tissue, liver, bone marrow) that drive insulin
  resistance, disrupted fat storage, chronic low-grade inflammation, and altered hormone
  signaling, and how these changes make the heart and blood vessels more vulnerable. The role's
  two core duties are (a) end-to-end research data management: conception, curation,
  structuring, data flow control, transformation, and enrichment of multi-omics research data
  into a usable resource for integrative analysis, and (b) developing training material on good
  scientific practice in data management. Required skills include confident Linux shell use and
  Python including a "data science stack": REST APIs, databases, message queuing systems, ETL
  workflows.
- A PhD position in computational biology at a nephrology/cardiovascular research center,
  studying how the hematopoietic system links aging, cardiovascular, and kidney disease across
  organs at single-cell resolution and biobank scale. Core duties include integrating in-house and
  public single-cell RNA-seq data, analyzing large-scale genomic/proteomic/clinical data,
  building reproducible and scalable computational pipelines, and collaborating with
  experimental and clinical researchers. Required skills include Python or R, prior single-cell
  RNA-seq analysis (Seurat-type workflows), reproducible coding practice, and cloud-environment
  experience.

The project below is a small, honestly-scoped, originally-built system inspired by the *type* of
science and infrastructure both postings describe. It is not affiliated with, and must never claim
to be affiliated with, either institution or consortium. All documentation must describe it as
"inspired by public research on cardiometabolic disease" and nothing more specific than that. Never use
em dash in any point of the project.

## 2. Scientific framing (the story this project tells)

Type 2 diabetes (T2D) and cardiovascular disease share upstream biology: metabolic dysfunction
in a small set of organs (liver, adipose tissue, gut, and the bone-marrow/hematopoietic
compartment) can each independently contribute to insulin resistance and systemic inflammation,
and the overlap between these organs' disturbed pathways is a plausible route to the elevated
cardiovascular risk seen in T2D patients.

This project builds a small multi-tissue transcriptomics data platform to explore that overlap:

1. Ingest public RNA-seq expression data for the four organs above.
2. Curate it into a well-structured, documented, queryable database (this is the "data steward"
   half of the project).
3. Run differential expression and pathway enrichment per tissue where disease-labeled data is
   available, and compare which pathways recur across tissues (the "crosstalk" analysis).
4. Apply unsupervised learning across the integrated multi-tissue signature to see whether
   samples separate into biologically interpretable subgroups, echoing (at toy scale) the real
   goal of large consortia: finding molecular subtypes that could sharpen risk prediction.
5. Expose all of the above through a REST API and a small set of async, queue-driven analysis
   jobs, so the system behaves like a real research data platform, not a one-off script.
6. (Stretch goal) Add a single-cell RNA-seq module on one public hematopoietic/immune dataset,
   to demonstrate the adjacent skill set the second job posting calls for.

## 3. Non-negotiable constraints

- Public, de-identified data only. Never use or simulate real patient-identifiable data.
- No dataset, finding, or figure may overstate what small-N public data actually supports. Every
  results page/notebook must state sample sizes and explicitly flag this as a portfolio-scale
  analysis, not a validated clinical finding.
- Every dataset used must be cited with its accession number, source repository, and original
  publication (if known) in `DATA_SOURCES.md`.
- Reproducibility over cleverness: anyone must be able to `docker compose up` and reproduce the
  full pipeline from raw public data to API-served results.

## 4. Phase 0: dataset selection and validation (do this before writing pipeline code)

Do not hardcode dataset assumptions from this file without verifying them first. Web search and
NCBI E-utilities access are available; use them.

Recommended two-tier data strategy:

**Tier A — cross-tissue baseline (engineering backbone).** Use the GTEx (Genotype-Tissue
Expression) project via the public GTEx Portal REST API (`https://gtexportal.org/api/v2/`,
confirm current base URL and endpoints before use) to pull bulk RNA-seq summary expression for
four tissues that map onto the four "promoter organs": Liver, Adipose - Subcutaneous, Small
Intestine - Terminal Ileum, and Whole Blood (as a practical, well-annotated proxy for the
bone-marrow/hematopoietic compartment; document this substitution explicitly and honestly as a
proxy, not a claim of equivalence). GTEx has no disease case/control labels, so it is used only to
build and validate the ingestion/database/API/orchestration architecture across four real tissues
via a real, well-documented, stable REST API. This also directly demonstrates "consuming a REST
API" as an ingestion source, distinct from "building a REST API" as the platform's output.

**Tier B — disease signal (the actual science).** Layer in at least one public case/control
(disease vs. healthy) bulk RNA-seq dataset from NCBI GEO per tissue, to generate the real
differential expression and cross-tissue crosstalk analysis. Candidates found via search, to be
verified for exact sample design, condition labels, and accessibility before use (fetch each
accession's summary via the NCBI GEO E-utilities REST API and record it in `DATA_SOURCES.md`
before writing any ingestion code against it):

- Liver (NAFLD/insulin resistance, plausible T2D-adjacent phenotype): GSE126848.
- Adipose tissue (subcutaneous, obesity/metabolic phenotype): GSE162653; also consider
  GSE176171 (single-cell adipose atlas) if extending to Tier C.
- Gut/intestinal (obesity or metabolic phenotype): candidates to verify include GSE111889,
  GSE160729, GSE228532, GSE122515 — check each for tissue type, human origin, condition labels,
  and RNA-seq (not microarray) before choosing.
- Bone marrow / hematopoietic / immune proxy (aging or inflammation phenotype): candidates to
  verify include GSE75478 (single-cell HSPCs) and GSE213516 (PBMC single-cell); if no suitable
  bulk RNA-seq case/control dataset is found, whole blood from GTEx plus one PBMC dataset with
  clear condition labels is an acceptable, documented substitute.

If any candidate above turns out to be unsuitable on inspection (wrong species, microarray
instead of RNA-seq, no usable condition labels, access restricted), replace it and document the
substitution and reasoning in `DATA_SOURCES.md`. It is fine, and expected, for the final dataset
list to differ from this draft — record what changed and why.

**Tier C — stretch goal, single-cell.** If time allows, add one public single-cell RNA-seq dataset
(e.g. an adipose or hematopoietic single-cell atlas such as GSE176171 or GSE75478, verified as
above) analyzed with `scanpy`, to demonstrate the single-cell skill set explicitly called for in
the second job posting. Keep this cleanly separable from the core bulk-RNA-seq platform so it can
be skipped without breaking anything if time is limited.

## 5. Architecture overview

```
                    ┌────────────────────┐
  Public sources ─► │  ETL orchestrator   │─► curated, versioned
  (GTEx REST API,   │  (Prefect flows)    │   Postgres database
  GEO E-utilities)  └────────┬───────────┘        │
                              │ triggers            │ read/write
                              ▼                     ▼
                     ┌──────────────────┐   ┌───────────────┐
                     │ Message queue     │   │  FastAPI      │
                     │ (RabbitMQ +       │◄──┤  REST service │◄── recruiters /
                     │  Celery workers)  │   │  (OpenAPI docs)│    reviewers /
                     └────────┬─────────┘   └───────┬───────┘    the developer
                              │ run                   │ serve
                              ▼                       ▼
                     ┌──────────────────┐   ┌───────────────┐
                     │ Analysis workers  │   │ Results /     │
                     │ (pydeseq2, gseapy,│   │ notebooks /    │
                     │  scikit-learn,    │   │ figures        │
                     │  optional scanpy) │   └───────────────┘
                     └──────────────────┘
```

Everything runs locally via `docker-compose.yml`: `postgres`, `rabbitmq`, `api` (FastAPI +
Uvicorn), `worker` (Celery), and a `prefect` service or local Prefect agent for orchestration.

## 6. Component 1 — Database ("Datenbanken")

Use PostgreSQL with SQLAlchemy (2.x style) and Alembic migrations. Sketch the schema as a
starting point, refine as needed:

- `datasets` — accession, source (GTEx/GEO), title, organism, assay type, citation, license,
  ingestion date, checksum of raw file(s).
- `samples` — id, dataset_id (FK), tissue, condition (e.g. control/disease), donor metadata
  (age bracket, sex, BMI category — only if provided by the source and non-identifying),
  library/QC metrics.
- `genes` — Ensembl gene id, symbol, biotype, chromosome (a small reference table, loaded once).
- `expression_values` — sample_id (FK), gene_id (FK), raw_count, normalized_value (e.g. TPM or
  DESeq2 size-factor-normalized), unit. Index appropriately; this table will be the largest.
- `analysis_runs` — id, type (differential_expression / enrichment / clustering / crosstalk),
  parameters (JSON), status, submitted_at, completed_at, triggered_via (api/etl), result
  reference.
- `differential_expression_results` — analysis_run_id (FK), gene_id (FK), log2FoldChange, pvalue,
  padj, tissue.
- `crosstalk_modules` — cross-tissue gene/pathway groupings discovered by the clustering step,
  with member genes and the tissues they recur in.

Every table that stores derived data must reference the `analysis_runs` row that produced it, so
every number in the API is traceable back to the exact code version and parameters that generated
it (basic provenance — this is the "data steward" discipline the project is meant to demonstrate).

## 7. Component 2 — ETL / workflow orchestration ("ETL Workflows", "Datenflusssteuerung")

Use Prefect (2.x/3.x, confirm current stable API) for orchestration; it is lighter-weight than
Airflow for a solo portfolio project while still being a real, recognizable orchestration tool.
Note in the README that Apache Airflow was considered and Prefect chosen for faster local
iteration; this shows the decision was deliberate, not a skill gap.

Build flows as composable tasks:

1. `fetch_gtex_tissue(tissue)` — pull expression data for one tissue via the GTEx REST API.
2. `fetch_geo_dataset(accession)` — pull one GEO series' supplementary count matrix and sample
   metadata (via GEO E-utilities / direct FTP as appropriate); parse and validate.
3. `qc_and_normalize(raw_counts, metadata)` — basic QC (library size, detected-gene count
   thresholds), normalization (e.g. DESeq2-style median-of-ratios via `pydeseq2`, or TPM for
   GTEx-derived data), explicit documentation of any samples dropped and why.
4. `load_to_warehouse(...)` — idempotent upsert into Postgres, with a checksum/version check so
   re-running the flow on unchanged source data is a no-op.
5. `trigger_analysis(...)` — enqueue the relevant Celery task(s) once new curated data lands.

Each flow run's inputs, parameters, and outcome should be logged and (ideally) queryable, so the
"data flow control" duty from the job posting is genuinely demonstrated, not just implied.

## 8. Component 3 — Message queue ("Message Queuing Systeme")

Use RabbitMQ as the broker with Celery workers in Python. Queue and run, as discrete asynchronous
tasks (not inline in the API request/response cycle):

- `run_differential_expression(tissue, dataset_id)` — `pydeseq2`-based DE analysis, condition vs.
  control, Benjamini-Hochberg FDR correction, results written to
  `differential_expression_results`.
- `run_pathway_enrichment(analysis_run_id)` — `gseapy` enrichment (e.g. against KEGG/Reactome/GO
  gene sets) on the DE result's significant genes.
- `run_crosstalk_discovery()` — across all tissues with completed DE results, identify genes/
  pathways recurring in ≥2 tissues, and run an unsupervised step (e.g. hierarchical clustering or
  NMF on a tissue-by-pathway enrichment matrix) to surface candidate cross-organ modules.
- `run_subtype_clustering()` — integrate normalized expression across tissues per matched donor
  where possible (or per-tissue if donors don't match across datasets — document which case
  applies), and cluster samples with a documented, justified method (e.g. k-means with a
  silhouette-score-selected k, or a simple autoencoder if you want to demonstrate deep learning;
  justify the choice against the data's actual sample size rather than defaulting to something
  fashionable).

The API should be able to submit a task, return a task/analysis id immediately, and offer a
status/result endpoint to poll — real async job handling, not a disguised synchronous call.

## 9. Component 4 — REST API ("REST APIs")

Use FastAPI (auto-generated OpenAPI/Swagger docs are themselves a portfolio asset). Suggested
endpoints:

- `GET /datasets` — list ingested datasets with citation/provenance metadata.
- `GET /tissues/{tissue}/genes/{gene}/expression` — expression values for a gene in a tissue,
  optionally filtered by condition.
- `POST /analyses` — submit a new analysis job (type + parameters), returns a job id (enqueues to
  Celery).
- `GET /analyses/{id}` — job status and, once complete, a link to results.
- `GET /crosstalk/modules` — the discovered cross-tissue gene/pathway modules.
- `GET /health` — basic liveness/readiness check, DB and broker connectivity.

Use Pydantic models for request/response validation, versility the API (`/api/v1/...`), and
generate the OpenAPI docs page as the primary "try it live" artifact for anyone reviewing the
project.

## 10. Component 5 — bioinformatics / ML analysis core

This is the part that has to read as genuinely expert-level, not templated:

- Differential expression via `pydeseq2` (the actively maintained Python port of DESeq2), with
  correct handling of size factors, dispersion estimation, and multiple-testing correction
  (Benjamini-Hochberg). Do not use a naive t-test on normalized counts as the primary method;
  that is a common giveaway of surface-level bioinformatics knowledge.
- Pathway/gene-set enrichment via `gseapy` against recognized gene sets (GO Biological Process,
  KEGG, Reactome, or MSigDB hallmark sets). Report enrichment with FDR-corrected significance,
  not raw p-values.
- Cross-tissue integration: build a tissue × pathway enrichment-score matrix from the per-tissue
  DE + enrichment results, and use that (not raw expression, which won't be comparable across
  independent studies/platforms) as the basis for the crosstalk and subtype-discovery clustering.
  Explicitly explain in the docs why raw cross-study expression values are not directly
  comparable and enrichment-score-based integration is the more defensible approach — this kind
  of reasoning is exactly what distinguishes a genuinely knowledgeable candidate.
- If Tier C (single-cell) is built: use `scanpy` for QC (mitochondrial fraction, doublet
  filtering), normalization, clustering (Leiden), and cell-type annotation via marker genes or a
  reference-based method; keep this module's code and docs clearly separated from the bulk-RNA-
  seq core.
- Every analysis notebook/report must state its statistical assumptions and limitations (sample
  size, batch effects between independently-sourced datasets, lack of matched donors across
  tissues where applicable) in plain language.

## 11. Engineering and reproducibility standards

- `docker-compose.yml` bringing up Postgres, RabbitMQ, the API, Celery worker(s), and (if
  containerized) Prefect — one command to a fully working local stack.
- Dependency pinning via `pyproject.toml` (Poetry or `uv`) with a lockfile.
- Type hints throughout; `mypy` in CI.
- `pytest` test suite covering: API endpoint contracts, ETL task idempotency, and at least one
  statistical sanity check on the DE pipeline (e.g. run it on a synthetic dataset with a known
  injected effect and assert it is recovered).
- `ruff` + `black` (or `ruff format`) and pre-commit hooks.
- GitHub Actions CI: lint, type-check, test on every push.
- Structured logging (not print statements) throughout ETL and worker code.
- `.env.example` for configuration; use `pydantic-settings` for typed config loading, never commit
  real secrets (this project shouldn't need any, since all data sources are public).

## 12. Documentation and data-stewardship deliverables

These map directly to the "good scientific practice in data management" duty referenced in
Section 1, and are as important to the portfolio's credibility as the code itself:

- `README.md` — project pitch, architecture diagram, quickstart (`docker compose up`), and a
  short "why these design choices" section.
- `DATA_SOURCES.md` — every dataset used: accession, repository, organism, assay, license,
  citation, and a one-line note on why it was chosen (or, for anything from Section 4 that got
  swapped out, what replaced it and why).
- `DATA_MANAGEMENT_PLAN.md` — a short, honest FAIR-principles-style document: how data is
  identified (accessions), curated (the ETL steps and QC thresholds), structured (the schema),
  and how provenance is preserved (the `analysis_runs` linkage). Frame this explicitly as a small
  demonstration of the kind of training material a data steward role would be expected to produce
  for a research group, without claiming it as a real deliverable for any institution.
- One narrative notebook (Jupyter or marimo) that walks through the biological story end to end —
  from raw data to the cross-tissue crosstalk finding — with figures, meant to be the first thing
  a recruiter or hiring manager opens.

## 13. Suggested build order

1. Scaffolding: repo structure, `docker-compose.yml`, Postgres + Alembic migrations for the core
   schema, CI skeleton.
2. Tier A ingestion: GTEx REST API client, ETL flow for the four baseline tissues, load into the
   database. Get the FastAPI `/datasets` and expression-query endpoints working against this
   before adding complexity.
3. Add RabbitMQ + Celery; move at least one operation (even a placeholder) to an async task to get
   the queue wiring proven out early.
4. Tier B ingestion: GEO dataset validation and ingestion for one tissue (liver) end to end,
   including the real `pydeseq2` differential expression task, before replicating to the other
   three tissues.
5. Pathway enrichment task, then the cross-tissue crosstalk and subtype-clustering tasks.
6. Full REST API surface, OpenAPI docs polish, `/health` endpoint.
7. Documentation pass: `DATA_SOURCES.md`, `DATA_MANAGEMENT_PLAN.md`, README, architecture diagram.
8. Test coverage and CI hardening.
9. (Stretch) Tier C single-cell module.
10. Narrative notebook last, once there are real results to walk through.

## 14. Presentation notes for the finished repository

The README should read as a serious applied-science project, not a job-application prop: lead
with the scientific question and the architecture, not with "I built this to apply for X." It's
fine for a "Motivation" section near the end to briefly mention that the project was built to
develop and demonstrate skills relevant to bioinformatics data-platform roles, without naming or
quoting any specific job posting or institution. Include example API calls (curl or httpie) and at
least one screenshot or exported figure from the narrative notebook in the README itself, since
many reviewers will not clone the repo before deciding whether to look closer.

## 15. Git conventions

Conventional Commits style: `feat:`, `fix:`, `chore:`, `docs:`, `perf:`,
`refactor:`. Short summary line, blank line, then (if commit is big) 1–2 bullet points of
context — not exhaustive, just enough for someone scanning `git log` to
understand what changed and why.

## 16. Current progress (session continuity)

This section is the single source of truth for where the project actually stands. Read it first
at the start of every session before proposing next steps; it is expected to be more current than
your own memory of prior conversations.

**Working style note:** the developer is building this step by step, in small chunks, deliberately
(to practice their own skills alongside directing Claude Code). Do not jump ahead to later build-order
items unless explicitly asked, and keep each chunk small enough to explain clearly in a report.

### Status as of 2026-08-25

**Build-order position:** partway through step 1 (Scaffolding) of Section 13.

**Completed:**

- **Phase 1a — repo scaffolding (this session).** Repo structure, dependency/tooling config, a
  two-service `docker-compose.yml` backbone, and a CI skeleton. See the session report delivered
  with this chunk for full rationale. Concretely:
  - `src/cmo_platform/` package (`src` layout) with `config.py` — a `pydantic-settings`-based
    typed `Settings` object reading `DATABASE_URL`, `RABBITMQ_URL`, `API_V1_PREFIX`, `LOG_LEVEL`
    from environment / `.env`.
  - `pyproject.toml` — `uv`/PEP 621 project metadata, hatchling build backend, `ruff` (lint +
    format) and `mypy --strict` config, `pytest` config. Core deps: fastapi, uvicorn, sqlalchemy
    2.x, alembic, psycopg3, pydantic(-settings), structlog. Dev deps (as a `dependency-groups`
    group, not installed via extras): pytest, pytest-cov, mypy, ruff, pre-commit.
  - `docker-compose.yml` — `postgres` (16-alpine) and `rabbitmq` (3.13-management-alpine) only,
    both with healthchecks and a named volume for Postgres. `api`/`worker`/`prefect` services are
    intentionally deferred until there is application code for them to run (build-order steps 2
    and 3), so `docker compose up` never references a broken build.
  - `.env.example`, `.gitignore`, `.pre-commit-config.yaml` (ruff + ruff-format + mypy hooks),
    `.github/workflows/ci.yml` (uv sync, ruff check, ruff format --check, mypy, pytest via
    GitHub Actions), a placeholder `README.md` pointing here for the full spec/progress.
  - `tests/test_config.py` — two tests covering `Settings` defaults and env-var override.
  - Verified locally in a throwaway venv (no `uv`/`docker` installed on this machine): `ruff
    check`, `ruff format --check`, `mypy` (strict), and `pytest` all pass clean.
  - Committed as two commits (`feat: scaffold repo ...`, `docs: add project spec, progress
    tracker, git conventions`) and pushed to `origin/main` at
    https://github.com/leventdusunceli/cardiometabolic-omics-platform.

**Deliberate deviations / decisions made (not dictated verbatim by Section 13, filled in during
  build):**

- Split build-order step 1 into **1a (scaffolding, done)** and **1b (Postgres schema + Alembic
  migrations, not started)** rather than doing both in one chunk, to keep chunks small per the
  developer's stated preference.
- Chose `uv` as the package manager/build frontend (per Section 11's "Poetry or uv") and
  `ruff format` over `black` (Section 11 allows either) to keep tooling to one binary.
- `docker-compose.yml` currently only defines the infra backbone (Postgres, RabbitMQ). `api` and
  `worker` services, and a Prefect service/agent, are added in later chunks once there's a
  Dockerfile and application code for each — see Section 5's architecture diagram for the full
  target topology.
- Python package is named `cmo_platform` (import name) / `cmo-platform` (distribution name on
  PyPI-style metadata); not specified in the original spec, chosen for brevity.
- `uv`, `poetry`, and `docker` are **not installed** on the developer's machine as of this
  session. Scaffold correctness was verified with a plain `venv` + `pip install -e .` instead.
  `docker compose up` and `uv sync` are therefore still unverified end-to-end and should be
  checked once those tools are available.

**Not started yet (next up, per Section 13):**

1. Phase 1b — Postgres schema (Section 6 tables: `datasets`, `samples`, `genes`,
   `expression_values`, `analysis_runs`, `differential_expression_results`, `crosstalk_modules`)
   + Alembic migration setup, wired to the `DATABASE_URL` in `config.py`.
2. Build-order step 2 — GTEx REST API client, ETL flow for the four baseline tissues, `/datasets`
   and expression-query FastAPI endpoints.
3. Everything after that per Section 13, unchanged.

**How to resume:** confirm the developer wants to continue with Phase 1b (DB schema + Alembic),
or check for other direction, then proceed from there. Do not re-verify or redo the scaffolding
above unless something looks broken.

## 17. Instruction: keep this file's progress section current

Whenever you (Claude Code) complete a meaningful unit of work on this project — a git commit, a
finished build-order chunk, a design decision that deviates from this spec, or the end of a work
session — update Section 16 above with what changed, without waiting to be asked. Keep it accurate
rather than exhaustive: overwrite stale status instead of appending a growing log, keep a short
list of deliberate deviations/decisions (they matter for interview defensibility, per Section 0),
and always leave a clear "how to resume" pointer for the next session. This is what allows a new
session to pick up exactly where the previous one left off without the developer having to
re-explain context.
