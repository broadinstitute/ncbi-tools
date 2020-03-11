version 1.0

task Fetch_SRA_to_BAM {

    input {
        String  SRA_ID
        String  docker = "quay.io/dpark01/ncbi-tools"
    }

    command {
        /opt/docker/scripts/sra_to_ubam.sh ${SRA_ID} ${SRA_ID}.bam
    }

    output {
        File    reads_ubam = "${SRA_ID}.bam"
    }

    runtime {
        cpu:     4
        memory:  "15 GB"
        disks:   "local-disk 750 LOCAL"
        docker:  "${docker}"
    }
}
