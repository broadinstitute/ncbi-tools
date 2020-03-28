#!/bin/bash

set -x #-e -o pipefail #pipefail disabled because the elink may fail to retrieve representative genomes

if [ $# -lt 4 ]; then
    echo "This script gets fasta files from GenBank by taxid and desired sequence length."
    echo "Intended for aggregating fastas to serve as filtering/assembly references."
    echo "Usage: $0 ncbi_taxid seq_minlen seq_maxlen outputdir [return_count_limit]"
    echo "  Example: $0 txid2697049 29000 30800 ./references/"
    echo "  relies on entrez-direct"
    exit 1
fi

ncbi_taxid=${1#"txid"} # strip the prefix if it is present; we add it ourselves later to allow for either input style
seq_minlen="$2"
seq_maxlen="$3"
output_dir="$4"
return_count_limit="${5:-10000}"

script_start_date="$(date '+%Y-%m-%d-%H%M')"

# create the output dir and its parents if it does not exist
mkdir -p ${output_dir}

# get RefSeq
# accession:
esearch -db nuccore -query "txid${ncbi_taxid}[Organism:noexp] AND srcdb_refseq[PROP] AND (\"${seq_minlen}\"[SLEN] : \"${seq_maxlen}\"[SLEN])" | efetch -format acc > "${output_dir}/ncbi_refseq_for_txid${ncbi_taxid}.seq"
# fasta:
efetch -db nuccore -format fasta -id $(cat "${output_dir}/ncbi_refseq_for_txid${ncbi_taxid}.seq" | tr '\n' ',') > "${output_dir}/ncbi_refseq_for_txid${ncbi_taxid}.fasta"

# get accessions for representative assemblies (comparable to searching NCBI Genome)
# if no such representative sequences have been designated, touch the output
REPRESENTATIVE_GENOME_ACCESSIONS=$(esearch -db assembly -query "txid${ncbi_taxid}[Organism:noexp]" | efilter -query "representative[PROP]" | elink -target nuccore -name assembly_nuccore_refseq | efetch -format docsum | xtract -pattern DocumentSummary -element AccessionVersion Slen Title | sed 's/,.*//' | grep -v -i -e scaffold -e contig -e plasmid -e sequence -e patch | sort -t $'\t' -k 2,2nr | cut -f1 | tee "${output_dir}/ncbi_representative_genome_assemblies_for_txid${ncbi_taxid}.seq" | tr '\n' ',')
if [ ! -z "${REPRESENTATIVE_GENOME_ACCESSIONS}" ]; then
    echo "REPRESENTATIVE_GENOME_ACCESSIONS: ${REPRESENTATIVE_GENOME_ACCESSIONS}"
    efetch -db nuccore -format fasta -id "${REPRESENTATIVE_GENOME_ACCESSIONS}" > "${output_dir}/ncbi_representative_genome_assemblies_for_txid${ncbi_taxid}.fasta"
else
    touch "${output_dir}/ncbi_representative_genome_assemblies_for_txid${ncbi_taxid}.fasta"
fi

# get all entries from GenBank
#accessions:
esearch -db nuccore -query "txid${ncbi_taxid}[Organism:noexp] AND (\"${seq_minlen}\"[SLEN] : \"${seq_maxlen}\"[SLEN])" | efetch -stop "${return_count_limit}" -format acc > "${output_dir}/ncbi_all_genbank_seq_for_txid${ncbi_taxid}_as_of_${script_start_date}.seq"
#fastas:
efetch -db nuccore -format fasta -id $(cat "${output_dir}/ncbi_all_genbank_seq_for_txid${ncbi_taxid}_as_of_${script_start_date}.seq" | tr '\n' ',') > "${output_dir}/ncbi_all_genbank_seq_for_txid${ncbi_taxid}_as_of_${script_start_date}.fasta"
