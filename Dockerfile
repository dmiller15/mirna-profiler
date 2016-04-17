FROM ubuntu:14.04
MAINTAINER Daniel Miller <dmiller15@uchicago.edu>

ENV mirna-profiler 0.25

USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --force-yes \
    ant \
    cmake \
    default-jdk \
    gcc \
    git \
    libpq-dev \
    libdbd-pg-perl \
    openjdk-7-jre-headless \
    poppler-utils \
    postgresql-client \
    python-pip \
    python-virtualenv \
    python3-dev \
    python3-pip \
    r-base \
    s3cmd \
    time \
    wget \
    samtools
 
RUN adduser --disabled-password --gecos '' ubuntu && adduser ubuntu sudo && echo "ubuntu    ALL=(ALL)   NOPASSWD:ALL" >> /etc/sudoers.d/ubuntu

ENV HOME /home/ubuntu

USER ubuntu
RUN mkdir ${HOME}/bin
WORKDIR ${HOME}/bin

# Get and install genetorrent
RUN wget https://cghub.ucsc.edu/software/downloads/GeneTorrent/3.8.7/genetorrent-common_3.8.7-ubuntu2.207-14.04_amd64.deb \
&& wget https://cghub.ucsc.edu/software/downloads/GeneTorrent/3.8.7/genetorrent-download_3.8.7-ubuntu2.207-14.04_amd64.deb

ENV PATH ${PATH}:${HOME}/bin/mirna/v0.2.7/code/annotation:${HOME}/bin/mirna/v0.2.7/code/library_stats:${HOME}/bin/mirna/v0.2.7/code/custom_output/tcga

USER root
RUN dpkg -i --force-depends ${HOME}/bin/genetorrent-*.deb \
    && apt-get update \
    && apt-get -f install -y

RUN pip install s3cmd --user
RUN pip3 install sqlalchemy pandas numpy

USER ubuntu
WORKDIR ${HOME}/bin

# Get and install the miRNA profiler
RUN git clone -b develop https://github.com/dmiller15/mirna-profiler.git

USER root
WORKDIR ${HOME}
