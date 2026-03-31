# AGENTS.md

This document provides guidance for AI assistants (Claude Code, GitHub Copilot, etc.) working on this repository.

## Overview

ncbi-tools is a Docker container image packaging NCBI bioinformatics command-line tools for use in WDL/Cromwell genomics pipelines. It is primarily used on the Terra platform (app.terra.bio) as a runtime container for batch pipeline tasks.

The container is intentionally simple: it bundles a set of NCBI tools, a few utility scripts, and a TSV converter. There is no application code, no test suite, and no complex build system.

---

## Repository Structure

```
ncbi-tools/
├── Dockerfile                      # Container definition (micromamba base)
├── env.yaml                        # Conda/micromamba dependencies
├── install-tsv_converter.sh        # Installs Asymmetrik broad-tsv-converter (Node.js app)
├── scripts/
│   ├── biosample-fetch_attributes.py   # Fetch BioSample metadata from NCBI
│   ├── fetch_fastas_by_taxid_seqlen.sh # Fetch FASTA sequences by taxonomy ID
│   └── sra_to_ubam.sh                  # Convert SRA data to unmapped BAM
├── WDL/
│   └── task-sra_to_ubam.wdl        # WDL task wrapping sra_to_ubam.sh
├── .github/workflows/
│   └── docker.yml                  # CI: multi-arch Docker build + Trivy scan
├── .trivy-ignore-policy.rego       # Trivy CVSS-based ignore policy for batch containers
├── .trivyignore                    # Per-CVE Trivy exceptions
├── README.md                       # User-facing documentation
└── LICENSE                         # BSD 3-Clause
```

---

## Docker Image

### Base Image

The Dockerfile uses `mambaorg/micromamba` as its base image (Ubuntu LTS variant). This provides the `micromamba` package manager for installing conda packages without needing a full Miniconda/Anaconda installation.

### Dependency Management

All bioinformatics tools are installed via micromamba from conda-forge and bioconda channels. Dependencies are declared in `env.yaml` with `>=` minimum version pins (except Python, which is pinned to a major.minor version).

To add or update a dependency, edit `env.yaml` and rebuild the image.

### TSV Converter

The Asymmetrik broad-tsv-converter is a Node.js application installed from a pinned GitHub commit via `install-tsv_converter.sh`. Node.js itself is provided by the `nodejs` conda package (not from the base image). The converter is installed to `/opt/converter/`.

### sra-tools Quality Score Configuration

**Important:** Newer versions of sra-tools default to "simplified" quality scores (all bases set to Q30) to reduce download sizes. This is unsuitable for most analysis pipelines. The Dockerfile runs `vdb-config --simplified-quality-scores no` to preserve original quality scores. This setting is baked into the image so all users get correct quality scores by default.

Background: https://ncbiinsights.ncbi.nlm.nih.gov/2021/10/19/sra-lite/

If sra-tools is updated, verify that quality scores are being preserved correctly in `sam-dump` output.

---

## Scripts

### `biosample-fetch_attributes.py`

Python script that fetches BioSample metadata from NCBI using BioPython's Entrez module. Outputs both JSON and TSV formats.

**Required argument:** `--email` (NCBI Entrez API requires an email address for all requests).

Usage: `biosample-fetch_attributes.py --email user@example.com SAMN12345 SAMN67890 output_basename`

### `sra_to_ubam.sh`

Bash script that fetches reads from SRA and converts them to an unmapped BAM file with properly formatted read groups. Uses `esearch`, `efetch`, `sam-dump`, `samtools`, and `picard`.

Usage: `sra_to_ubam.sh SRA_ID output.bam`

### `fetch_fastas_by_taxid_seqlen.sh`

Bash script that retrieves FASTA sequences from NCBI by taxonomy ID and sequence length range. Fetches from RefSeq, representative genomes, and GenBank.

---

## CI/CD

### GitHub Actions Workflow (`.github/workflows/docker.yml`)

The workflow builds and pushes multi-architecture Docker images on every push and scans them for vulnerabilities.

**Triggers:**
- Push to any branch or tag
- Pull requests to main
- Weekly scheduled scan (Mondays 06:00 UTC)
- Manual dispatch

**Jobs:**
1. **build**: Builds `linux/amd64` and `linux/arm64` images using QEMU + Docker Buildx. Pushes to the configured container registry on push events (not on PRs).
2. **scan**: Pulls the built image and runs Trivy vulnerability scanning. Results are uploaded to the GitHub Security tab as SARIF.

### Container Registry

The workflow always pushes to GitHub Container Registry (GHCR) using the built-in `GITHUB_TOKEN`. It can optionally also push to a second registry (e.g., quay.io) by setting repository variables and secrets:
- Variables: `REGISTRY` (e.g., `quay.io`), `IMAGE_NAME` (e.g., `broadinstitute/ncbi-tools`)
- Secrets: `REGISTRY_USERNAME`, `REGISTRY_PASSWORD`

When configured, every push produces tags in both registries simultaneously.

### Trivy Scanning

Two-tier vulnerability filtering:
1. **`.trivy-ignore-policy.rego`**: Rego policy that filters out CVE classes inapplicable to batch pipeline containers (physical access required, adjacent network, local + user interaction, etc.). Supports both CVSS v3.1 and v4.0.
2. **`.trivyignore`**: Per-CVE exceptions with individual justifications.

The scan runs in two formats:
- **Table**: Human-readable, fails the workflow on CRITICAL/HIGH findings
- **SARIF**: Machine-readable, uploaded to GitHub Security tab for tracking

---

## WDL Task

`WDL/task-sra_to_ubam.wdl` defines a Cromwell/WDL task that wraps `sra_to_ubam.sh`. It extracts full metadata from SRA including sequencing center, platform, model, BioSample accession, library ID, run date, collection date, strain, collector, and geographic location.

The default docker image is `ghcr.io/broadinstitute/ncbi-tools`. Override via the `docker` input parameter.

---

## Common Operations

### Adding a conda dependency

1. Add the package to `env.yaml`
2. Rebuild: `docker build -t ncbi-tools .`
3. Push to trigger CI

### Updating the TSV converter

Update `ASYMMETRIK_REPO_COMMIT` in the Dockerfile to the desired commit hash.

### Updating sra-tools

When updating sra-tools, verify quality score behavior:
```bash
# Inside the container:
sam-dump --unaligned SRR_ACCESSION | head -1000 | awk '{print $11}' | sort -u
# Should show varied quality strings, NOT all identical Q30
```

### Running tests

Tests run inside the Docker container (they require the converter and Node.js):

```bash
# Build the image first
docker build -t ncbi-tools .

# Run tests
docker run --rm -v $(pwd)/tests:/work/tests ncbi-tools \
    bash -c "cd /work && python -m pytest tests/ -v"
```

Tests are also run automatically in CI after each Docker build.

### Building locally

```bash
# Single architecture (current platform)
docker build -t ncbi-tools .

# Multi-architecture
docker buildx build --platform linux/amd64,linux/arm64 -t ncbi-tools .
```
