FROM quay.io/jeremiahsavage/cdis_base

USER root
RUN apt-get update && apt-get install -y --force-yes \
    libpq-dev \
    openjdk-8-jre-headless \
    s3cmd \
    libdbd-pg-perl \
    r-base \
    samtools

USER ubuntu
ENV HOME /home/ubuntu

ENV mirna-profiler 0.42

RUN mkdir ${HOME}/bin
WORKDIR ${HOME}/bin

RUN git clone -b develop https://github.com/dmiller15/mirna-profiler.git

RUN /bin/bash -c "source ${HOME}/.local/bin/virtualenvwrapper.sh \
    && source ~/.virtualenvs/p3/bin/activate \
    && cd ~/bin/mirna-profiler \
    && pip install -e ." 

WORKDIR ${HOME}
