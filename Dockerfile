FROM mambaorg/micromamba:2.4.0-ubuntu24.04

LABEL maintainer="Daniel Park <dpark@broadinstitute.org>"

# Install system packages needed for the TSV converter build
USER root
RUN apt-get update && \
    apt-get install -y -qq --no-install-recommends \
        ca-certificates git wget curl locales && \
    locale-gen en_US.UTF-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# Set default locale to en_US.UTF-8
ENV LANG="en_US.UTF-8" LANGUAGE="en_US:en" LC_ALL="en_US.UTF-8"

# Install conda dependencies
COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml
RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

# Enable conda environment activation for subsequent RUN commands
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# Add manually to PATH for all the image-users who override our entrypoint
ENV PATH="/opt/conda/bin:$PATH"

# Install Asymmetrik TSV converter
ENV ASYMMETRIK_REPO_COMMIT=af2d184da9da9fcc94c6a4d809210868bb8f3034
COPY --chown=$MAMBA_USER:$MAMBA_USER install-tsv_converter.sh /opt/docker/install-tsv_converter.sh
USER root
RUN /opt/docker/install-tsv_converter.sh
USER $MAMBA_USER

# Install scripts
COPY --chown=$MAMBA_USER:$MAMBA_USER scripts/* /opt/docker/scripts/

# Configure sra-tools to preserve original quality scores (not simplified Q30)
# See: https://github.com/broadinstitute/ncbi-tools/issues/15
RUN vdb-config --simplified-quality-scores no

# Verify key tools are available
RUN esearch -version && \
    samtools --version | head -1 && \
    python --version && \
    node --version

CMD ["/bin/bash"]
