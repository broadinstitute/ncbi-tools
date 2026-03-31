# ncbi-tools

[![Build and Push Docker Image](https://github.com/broadinstitute/ncbi-tools/actions/workflows/docker.yml/badge.svg)](https://github.com/broadinstitute/ncbi-tools/actions/workflows/docker.yml)

Docker image packaging NCBI bioinformatics tools for retrieving sequence data, metadata, and converting between formats. Designed for use as a runtime container in WDL/Cromwell genomics pipelines on platforms like Terra.

## Included Tools

- **entrez-direct** - NCBI E-utilities command-line tools (esearch, efetch, elink, etc.)
- **sra-tools** - SRA Toolkit (sam-dump, fasterq-dump, etc.)
- **samtools** - Tools for manipulating SAM/BAM files
- **picard** - BAM/SAM manipulation and analysis
- **biopython** - Python library for biological computation
- **perl-xml-simple** - Perl XML parsing (used by entrez-direct)
- **broad-tsv-converter** - Asymmetrik TSV converter for NCBI data

## Bundled Scripts

| Script | Description |
|--------|-------------|
| `sra_to_ubam.sh` | Fetch SRA reads and convert to unmapped BAM with full read group metadata |
| `biosample-fetch_attributes.py` | Fetch and harmonize BioSample metadata from NCBI (JSON + TSV output) |
| `fetch_fastas_by_taxid_seqlen.sh` | Retrieve FASTA sequences from NCBI by taxonomy ID and sequence length |

## Usage

### Pull from GitHub Container Registry

```bash
docker pull ghcr.io/broadinstitute/ncbi-tools
```

### Run interactively

```bash
docker run --rm -it ghcr.io/broadinstitute/ncbi-tools bash
```

### Fetch BioSample metadata

```bash
docker run --rm -v $(pwd):/data ghcr.io/broadinstitute/ncbi-tools \
    python /opt/docker/scripts/biosample-fetch_attributes.py \
    --email your@email.org SAMN12345678 /data/output
```

### Convert SRA to unmapped BAM

```bash
docker run --rm -v $(pwd):/data ghcr.io/broadinstitute/ncbi-tools \
    /opt/docker/scripts/sra_to_ubam.sh SRR1234567 /data/output.bam
```

### Use in WDL pipelines

See [`WDL/task-sra_to_ubam.wdl`](WDL/task-sra_to_ubam.wdl) for a ready-to-use WDL task definition.

## Multi-Architecture Support

The image is built for both `linux/amd64` (Intel/AMD) and `linux/arm64` (Apple Silicon, ARM servers). Docker will automatically pull the correct architecture for your platform.

## Modifying the Environment

Edit `env.yaml` to add or remove conda packages, then rebuild:

```bash
docker build -t ncbi-tools .
```
