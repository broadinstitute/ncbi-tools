#!/bin/bash

set -e -o pipefail

if [ $# -lt 2 ]; then
    echo "This script fetches reads from SRA as a BAM file with properly formatted read groups"
    echo "Usage: $0 SRA_ID OUTFILE"
    echo "  relies on entrez-direct, jq, samtools, and Picard"
    exit 1
fi

SRA_ID="$1"
OUTFILE="$2"

esearch -db sra -q "${SRA_ID}" | efetch -mode json -json > ${SRA_ID}.json

CENTER=`cat ${SRA_ID}.json | jq -r .EXPERIMENT_PACKAGE_SET.EXPERIMENT_PACKAGE.SUBMISSION.center_name`
PLATFORM=`cat ${SRA_ID}.json | jq -r '.EXPERIMENT_PACKAGE_SET.EXPERIMENT_PACKAGE.EXPERIMENT.PLATFORM | keys[] as $k | "\($k)"'`
MODEL=`cat ${SRA_ID}.json | jq -r ".EXPERIMENT_PACKAGE_SET.EXPERIMENT_PACKAGE.EXPERIMENT.PLATFORM.${PLATFORM}.INSTRUMENT_MODEL"`
SAMPLE=`cat ${SRA_ID}.json | jq -r '.EXPERIMENT_PACKAGE_SET.EXPERIMENT_PACKAGE.SAMPLE.IDENTIFIERS.EXTERNAL_ID|select(.namespace == "BioSample")|.content'`
LIBRARY=`cat ${SRA_ID}.json | jq -r .EXPERIMENT_PACKAGE_SET.EXPERIMENT_PACKAGE.EXPERIMENT.DESIGN.LIBRARY_DESCRIPTOR.LIBRARY_NAME`
RUNDATE=`cat ${SRA_ID}.json | jq -r '.EXPERIMENT_PACKAGE_SET.EXPERIMENT_PACKAGE.RUN_SET.RUN.SRAFiles|if (.SRAFile|type) == "object" then .SRAFile.date else [.SRAFile[]|select(.supertype == "Original")][0].date end' | cut -f 1 -d ' '`

sam-dump --unaligned --header ${SRA_ID} \
    | samtools view -bhS - \
    > temp.bam

picard AddOrReplaceReadGroups \
    I=temp.bam \
    O="$OUTFILE" \
    RGID=1 \
    RGLB="$LIBRARY" \
    RGSM="$SAMPLE" \
    RGPL="$PLATFORM" \
    RGPU="$LIBRARY" \
    RGPM="$MODEL" \
    RGDT="$RUNDATE" \
    RGCN="$CENTER" \
    VALIDATION_STRINGENCY=SILENT
