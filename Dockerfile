FROM node:lts-buster

LABEL maintainer "Daniel Park <dpark@broadinstitute.org>"

# non-interactive session just for build
ARG DEBIAN_FRONTEND=noninteractive

# install scripts
COPY install-*.sh /opt/docker/

# System packages, etc
RUN /opt/docker/install-apt_packages.sh

# Set default locale to en_US.UTF-8
ENV LANG="en_US.UTF-8" LANGUAGE="en_US:en" LC_ALL="en_US.UTF-8"

# install miniconda3 with our default channels and no other packages
ENV MINICONDA_PATH="/opt/miniconda" CONDA_DEFAULT_ENV="default"
RUN /opt/docker/install-miniconda.sh
ENV PATH="$MINICONDA_PATH/envs/$CONDA_DEFAULT_ENV/bin:$MINICONDA_PATH/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
RUN conda create -n $CONDA_DEFAULT_ENV python=3.7
RUN echo "source activate $CONDA_DEFAULT_ENV" >> ~/.bashrc
RUN hash -r

# install specific tools
COPY requirements-conda.txt /opt/docker
RUN /bin/bash -c "set -e; sync; conda install -y --quiet --file /opt/docker/requirements-conda.txt ; conda clean -y --all"

# install tsv converter
ENV ASYMMETRIK_REPO_COMMIT=af2d184da9da9fcc94c6a4d809210868bb8f3034
RUN /opt/docker/install-tsv_converter.sh

# install scripts
COPY scripts/* /opt/docker/scripts/

RUN /bin/bash -c "set -e; echo -n 'esearch version: '; esearch -version"

# set up entrypoint
CMD ["/bin/bash"]

