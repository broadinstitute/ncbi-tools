#!/bin/bash

set -ex -o pipefail

if [ $# -ne 4 ]; then
    echo "This script gets fasta files from GenBank by taxid and desired sequence length."
    echo "Intended for aggregating fastas to serve as filtering/assembly references."
    echo "Usage: $0 ncbi_taxid seq_minlen seq_maxlen outputdir"
    echo "  Example: $0 txid2697049 29000 30800 ./references/"
    echo "  relies on entrez-direct"
    exit 1
fi

ncbi_taxid=${1#"txid"} # strip the prefix if it is present; we add it ourselves later to allow for either input style
seq_minlen="$2"
seq_maxlen="$3"
output_dir="$4"

# create the output dir and its parents if it does not exist
mkdir -p ${output_dir}

# get RefSeq
# accession:
REFSEQ_ACCESSIONS=$(esearch -db nuccore -query "txid${ncbi_taxid}[Organism:noexp] AND srcdb_refseq[PROP] AND (\"${seq_minlen}\"[SLEN] : \"${seq_maxlen}\"[SLEN])" | efetch -format acc | tee "${output_dir}/refseq_for_txid${ncbi_taxid}.seq" | tr '\n' ' ')
# fasta:
esearch -db nuccore -query "txid${ncbi_taxid}[Organism:noexp] AND srcdb_refseq[PROP] AND (\"${seq_minlen}\"[SLEN] : \"${seq_maxlen}\"[SLEN])" | efetch -format fasta > "${output_dir}/refseq_for_txid${ncbi_taxid}.fasta"

# get all entries
# accessions:
esearch -db nuccore -query "txid${ncbi_taxid}[Organism:noexp] AND (\"${seq_minlen}\"[SLEN] : \"${seq_maxlen}\"[SLEN])" | efetch -format acc > "${output_dir}/all_seq_for_txid${ncbi_taxid}_on_genbank_as_of_$(date '+%Y-%m-%d-%H%M').seq"
# fastas:
esearch -db nuccore -query "txid${ncbi_taxid}[Organism:noexp] AND (\"${seq_minlen}\"[SLEN] : \"${seq_maxlen}\"[SLEN])" | efetch -format fasta > "${output_dir}/all_seq_for_txid${ncbi_taxid}_on_genbank_as_of_$(date '+%Y-%m-%d-%H%M').fasta"

