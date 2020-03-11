FROM ubuntu:bionic-20200219

LABEL maintainer "Daniel Park <dpark@broadinstitute.org>"

COPY install-*.sh /opt/docker/

# System packages, etc
RUN /opt/docker/install-apt_packages.sh

# Set default locale to en_US.UTF-8
ENV LANG="en_US.UTF-8" LANGUAGE="en_US:en" LC_ALL="en_US.UTF-8"

# install miniconda3 with our default channels and no other packages
ENV MINICONDA_PATH="/opt/miniconda" CONDA_DEFAULT_ENV="default"
RUN /opt/docker/install-miniconda.sh
RUN conda create -n $CONDA_DEFAULT_ENV python=3.6
RUN echo "source activate $CONDA_DEFAULT_ENV" > ~/.bashrc
RUN hash -r

# install NCBI Entrez tools and jq (json parser)
RUN conda install entrez-direct jq

# set up entrypoint
ENV PATH="$MINICONDA_PATH/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
CMD ["/bin/bash"]
