FROM ubuntu:14.04
MAINTAINER Daniel Miller <dmiller15@uchicago.edu>

USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --force-yes \
    ant \
    cmake \
    default-jdk \
    gcc \
    git \
    libpq-dev \
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
    mysql-server \
    samtools
 
WORKDIR /var/lib/mysql/

# Setup the partial UCSC Database
RUN rsync -avzP rsync://hgdownload.cse.ucsc.edu/mysql/hg38/knownGene.* ./hg38/ \
&& rsync -avzP rsync://hgdownload.cse.ucsc.edu/mysql/hg38/refGene.* ./hg38/ \
&& rsync -avzP rsync://hgdownload.cse.ucsc.edu/mysql/hg38/kgXref.* ./hg38/

RUN adduser --disabled-password --gecos '' ubuntu && adduser ubuntu sudo && echo "ubuntu    ALL=(ALL)   NOPASSWD:ALL" >> /etc/sudoers.d/ubuntu

ENV HOME /home/ubuntu

USER ubuntu
RUN mkdir ${HOME}/bin
WORKDIR ${HOME}/bin

# Get and install genetorrent
RUN wget https://cghub.ucsc.edu/software/downloads/GeneTorrent/3.8.7/genetorrent-common_3.8.7-ubuntu2.207-14.04_amd64.deb \
&& wget https://cghub.ucsc.edu/software/downloads/GeneTorrent/3.8.7/genetorrent-download_3.8.7-ubuntu2.207-14.04_amd64.deb

# Get all of the files for the mirbase database
RUN wget ftp://mirbase.org/pub/mirbase/CURRENT/database_files/tables.sql \
&& wget ftp://mirbase.org/pub/mirbase/CURRENT/database_files/mirna.txt.gz \
&& wget ftp://mirbase.org/pub/mirbase/CURRENT/database_files/mirna_species.txt.gz \
&& wget ftp://mirbase.org/pub/mirbase/CURRENT/database_files/mirna_chromosome_build.txt.gz \
&& wget ftp://mirbase.org/pub/mirbase/CURRENT/database_files/mirna_mature.txt.gz \
&& wget ftp://mirbase.org/pub/mirbase/CURRENT/database_files/mirna_pre_mature.txt.gz \
&& gunzip *.txt.gz


ENV PATH ${PATH}:${HOME}/bin/mirna/v0.2.7/code/annotation:${HOME}/bin/mirna/v0.2.7/code/library_stats:${HOME}/bin/mirna/v0.2.7/code/custom_output/tcga

USER root
RUN dpkg -i --force-depends ${HOME}/bin/genetorrent-*.deb \
    && apt-get update \
    && apt-get -f install -y

RUN pip install s3cmd --user
RUN pip3 install sqlalchemy pandas numpy

# Load the files for the mirbase
RUN service mysql start \
&& mysql -e "create database mirna_current" \
&& mysql mirna_current -e "source tables.sql" \
&& mysql mirna_current --local-infile=1 -e "load data local infile 'mirna.txt' into table mirna" \
&& mysql mirna_current --local-infile=1 -e "load data local infile 'mirna_species.txt' into table mirna_species" \
&& mysql mirna_current --local-infile=1 -e "load data local infile 'mirna_chromosome_build.txt' into table mirna_chromosome_build" \
&& mysql mirna_current --local-infile=1 -e "load data local infile 'mirna_mature.txt' into table mirna_mature" \
&& mysql mirna_current --local-infile=1 -e "load data local infile 'mirna_pre_mature.txt' into table mirna_pre_mature" \
&& service mysql stop

# Delete the table files
RUN rm *.txt *.sql

USER ubuntu
WORKDIR ${HOME}/bin

ENV mirna_profiler 0.16

# Get and install the miRNA profiler
RUN git clone -b develop https://github.com/dmiller15/mirna-profiler.git

USER root
WORKDIR ${HOME}
