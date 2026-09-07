# Cardiometabolic Crosstalk Omics Platform

A multi-tissue transcriptomics data platform exploring shared biology between type 2 diabetes
(T2D) and cardiovascular risk, inspired by public research on cardiometabolic disease.

**This is a preliminary, work-in-progress README** describing the project's aims and current
state. A full pitch, quickstart, and example API calls will land once the core pipeline is
working end to end.

## The biological problem

T2D and cardiovascular disease are usually taught as two separate conditions linked mainly
through shared risk factors like high blood sugar damaging blood vessels. A more current
mechanistic view, and the one this project is built around, is that several peripheral organs
actively generate the systemic state that puts the heart and blood vessels at risk, rather than
the cardiovascular system simply being a downstream victim of hyperglycemia. Four tissues do
most of this work, each through a distinct mechanism with a real evidence base:

- **Liver**: under chronic caloric and lipid oversupply, the liver accumulates fat, becomes
  inflamed, and oversecretes lipoproteins in a way that promotes a pro-atherogenic circulating
  lipid profile independent of shared risk factors (Duell et al., 2022, *Arterioscler Thromb Vasc
  Biol*).
- **Gut**: increased intestinal permeability under a high-fat, high-sugar diet raises circulating
  bacterial endotoxin, which is sufficient on its own to drive insulin resistance in animal models
  (Cani et al., 2007, *Diabetes*), with the gut-liver-systemic inflammation pathway reviewed in
  Albillos, de Gottardi, and Rescigno (2020, *J Hepatol*).
- **Adipose tissue**: under obesity, fat tissue shifts its secretory and immune profile toward a
  pro-inflammatory state, first linked to insulin resistance by Hotamisligil et al. (1993,
  *Science*) and shown to involve substantial immune cell infiltration by Weisberg et al. (2003,
  *J Clin Invest*).
- **Bone marrow / hematopoietic compartment**: blood-forming stem cells integrate systemic
  inflammatory and metabolic signals and adjust their output accordingly, a mechanism tied
  directly to cardiovascular risk in humans through the discovery that somatic mutations driving
  clonal expansion of blood stem cells are an independent risk factor for atherosclerotic disease
  (Jaiswal et al., 2017, *N Engl J Med*).

This project's actual, testable claim is narrower than "these organs cause heart disease": if the
four organs above are mechanistically linked in cardiometabolic disease as the literature
describes, their disease-associated gene expression signatures should show recurring,
overlapping pathway-level disturbances (shared inflammatory, lipid-handling, or insulin-signaling
programs) more than expected from independent, tissue-specific noise. That overlap is the
"crosstalk" the project name refers to: a hypothesis-generating, exploratory analysis built on
established mechanistic biology, not a mechanistic proof produced by this project itself.

**Note on scope**: whole blood is used as a practical proxy for the bone marrow / hematopoietic
compartment, since blood is the direct downstream output of that compartment and is what the
clinical clonal-hematopoiesis evidence above was actually measured from. This is stated
explicitly wherever it's used, not treated as a claim of tissue equivalence.

## What the platform does

1. Ingests public bulk RNA-seq expression data for the four tissues above, from two source tiers:
   a well-annotated, disease-label-free baseline (GTEx) used to validate the ingestion pipeline
   architecture, and one public case/control disease-vs-healthy dataset per tissue from NCBI GEO,
   which is what the actual differential expression analysis runs against.
2. Curates that data into a documented, queryable Postgres database, with every derived number
   traceable back to the exact analysis run that produced it.
3. Runs differential expression (via `pydeseq2`, the standard statistical model for RNA-seq count
   data) and pathway enrichment per tissue, then looks for which pathways recur across tissues.
4. Exposes the ingested data and analysis results through a REST API, with long-running analyses
   handled as asynchronous background jobs rather than blocking requests.

Every result this platform produces states its sample size and is framed explicitly as a
portfolio-scale, exploratory analysis, not a validated clinical or biological finding. Public
GEO sample sizes in this space are genuinely small (single-digit to low double-digit per group),
and that limitation is treated as something to disclose plainly, not smooth over.

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

Everything runs locally via Docker Compose. The database schema tracks datasets, samples, genes,
expression values, and analysis runs as first-class, linked records, so every DE result or
enrichment score in the API can be traced back to the exact data and parameters that produced it.

## Current status

- **Done**: repository scaffolding, CI, and the Postgres schema with migrations; ingestion of the
  GTEx baseline across all four tissues, served through a working REST API
  (`GET /datasets`, gene-expression queries); RabbitMQ and Celery wired end to end and proven with
  a real asynchronous job round-trip.
- **In progress**: ingestion of the four disease-signal datasets from GEO. All four have been
  validated (species, assay type, usable condition labels) and are documented in
  `DATA_SOURCES.md`. A working client parses GEO's raw data files, and the case/control mapping
  for the first tissue (liver) is built. Still to come for that tissue: quality control and
  normalization, loading into the database, and the actual `pydeseq2` differential expression
  run, before repeating the same pipeline for the remaining three tissues.
- **Not started**: pathway enrichment, cross-tissue crosstalk analysis, unsupervised subtype
  discovery, and the narrative notebook walking through the full biological story.

See `DATA_SOURCES.md` for the exact datasets used and their provenance.
