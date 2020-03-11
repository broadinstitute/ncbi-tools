version 1.0


task Fetch_SRA_to_BAM {
    input {
        String	SRA_ID
	String	docker = "quay.io/dpark01/ncbi-tools"
    }

    Int cpus = 4
    Int final_disk_space_gb = 700

    command {
	set -ex -o pipefail

	esearch -db sra -q "${SRA_ID}" | efetch -mode json -json > ${SRA_ID}.json

	CENTER=`cat ${SRA_ID}.json | jq -r '.EXPERIMENT_PACKAGE_SET.EXPERIMENT_PACKAGE.SUBMISSION.center_name'`
	PLATFORM=`cat ${SRA_ID}.json | jq -r '.EXPERIMENT_PACKAGE_SET.EXPERIMENT_PACKAGE.EXPERIMENT.PLATFORM | keys[] as $k | "\($k)"'`
	MODEL=`cat ${SRA_ID}.json | jq -r .EXPERIMENT_PACKAGE_SET.EXPERIMENT_PACKAGE.EXPERIMENT.PLATFORM.$PLATFORM.INSTRUMENT_MODEL`
	SAMPLE=`cat ${SRA_ID}.json | jq -r '.EXPERIMENT_PACKAGE_SET.EXPERIMENT_PACKAGE.SAMPLE.IDENTIFIERS.EXTERNAL_ID|select(.namespace == "BioSample")|.content'`
	LIBRARY=`cat ${SRA_ID}.json | jq -r '.EXPERIMENT_PACKAGE_SET.EXPERIMENT_PACKAGE.EXPERIMENT.DESIGN.LIBRARY_DESCRIPTOR.LIBRARY_NAME'`
	RUNDATE=`cat ${SRA_ID}.json | jq -r '.EXPERIMENT_PACKAGE_SET.EXPERIMENT_PACKAGE.RUN_SET.RUN.SRAFiles.SRAFile[]|select(.supertype == "Original")|.date'`
	
	sam-dump --unaligned --header ${SRA_ID} \
		| samtools view -bhS - \
		> temp.bam

	picard AddOrReplaceReadGroups \
		I=temp.bam O=${SRA_ID}.bam \
		RGLB="$LIBRARY" \
		RGSM="$SAMPLE" \
		RGPL="$PLATFORM" \
		RGPU="$LIBRARY" \
		RGPM="$MODEL" \
		RGDT="$RUNDATE" \
		VALIDATION_STRINGENCY=LENIENT \
		USE_JDK_DEFLATER=true USE_JDK_INFLATER=true
    }

    output {
	File	reads_ubam = "${SRA_ID}.bam"
    }

    runtime {
        cpu: cpus
        memory: "15 GB"
        disks: "local-disk 750 LOCAL"
        docker: "${docker}"
    }
}
