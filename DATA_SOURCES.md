# Data Sources

Every dataset ingested by this platform, its provenance, and why it was chosen.

## Tier A — cross-tissue baseline (GTEx)

Used to build and validate the ingestion/database/API/orchestration architecture across four
real tissues. GTEx carries no disease case/control labels, so it never feeds differential
expression — its role is architectural and descriptive-reference only.

| Field | Value |
|---|---|
| Accession | `gtex_v8_Liver`, `gtex_v8_Adipose_Subcutaneous`, `gtex_v8_Small_Intestine_Terminal_Ileum`, `gtex_v8_Whole_Blood` |
| Repository | GTEx Portal REST API v2 (`https://gtexportal.org/api/v2`) |
| Organism | Homo sapiens |
| Assay | Bulk RNA-seq, portal-aggregated median TPM across donors (GTEx release v8) |
| License | GTEx open-access summary data |
| Citation | GTEx Consortium, https://gtexportal.org |
| Why chosen | Four well-annotated tissues; Whole Blood used as a documented proxy for the bone-marrow/hematopoietic compartment. |

## Tier B — disease signal (GEO)

Case/control bulk RNA-seq, one dataset per tissue.

### Liver

| Field | Value |
|---|---|
| Accession | GSE126848 |
| Repository | NCBI GEO (BioProject PRJNA523510) |
| Organism | Homo sapiens |
| Assay | Bulk RNA-seq; raw counts in `GSE126848_Gene_counts_raw.txt.gz` |
| Samples | 57: Normal-weight (14), Obese (12), NAFL (15), NASH (16) |
| License | Public |
| Citation | PMID 30653341 |
| Why chosen | NAFLD/NASH, the closest available human liver metabolic-disease phenotype; framed as T2D-adjacent, not literal T2D. |

### Adipose

| Field | Value |
|---|---|
| Accession | GSE162653 |
| Repository | NCBI GEO |
| Organism | Homo sapiens |
| Assay | Bulk RNA-seq, white adipose tissue |
| Samples | 40; normal weight vs. obese, sampled at Week-0 and Week-12 of a fish-oil/corn-oil intervention |
| License | Public |
| Citation | PMID 33393630 |
| Why chosen | Matches the project's GTEx adipose tissue; real normal-weight-vs-obese phenotype at baseline. |

### Gut

| Field | Value |
|---|---|
| Accession | GSE306982 |
| Repository | NCBI GEO |
| Organism | Homo sapiens |
| Assay | Bulk RNA-seq, patient-derived jejunum organoids; raw counts in `GSE306982_merged_gene_count.tsv.gz` |
| Samples | 9: lean, obese, obese-hyperabsorptive |
| License | Public |
| Citation | PMID 41394425 |
| Why chosen | Closest available human gut-tissue metabolic-phenotype RNA-seq dataset. Small n — treated as exploratory. |

### Bone marrow / blood proxy

| Field | Value |
|---|---|
| Accession | GSE153315 |
| Repository | NCBI GEO |
| Organism | Homo sapiens |
| Assay | Bulk RNA-seq, Whole Blood; raw counts in `GSE153315_counts.txt.gz` |
| Samples | 30: 10 healthy controls, 20 Type 2 Diabetes patients |
| License | Public |
| Citation | GSE153315 |
| Why chosen | Direct, literal Type 2 Diabetes vs. healthy control labels; tissue matches the project's GTEx Whole Blood choice. |
