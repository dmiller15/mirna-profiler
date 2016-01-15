FROM ubuntu:15.04

ENV VERSION="1.3"
ENV NAME="samtools"

ENV URL="https://github.com/samtools/samtools/archive/${VERSION}.tar.gz"
#https://github.com/samtools/htslib/archive/1.2.1.tar.gz

RUN  apt-get update \
  && apt-get install -y wget \
  && apt-get install -y git

RUN  apt-get install -y build-essential \
  && apt-get install -y zlib1g-dev libncurses5-dev \
  && apt-get install -y libpng-dev

RUN  set -xe \
  && git clone --branch=develop https://github.com/samtools/htslib.git \
  && cd htslib \
  && make \
  && make test \
  && make install

RUN wget -q -O ${NAME}.tar.gz ${URL} && tar -zxvf ${NAME}.tar.gz && rm -f ./${NAME}.tar.gz && cd ${NAME}-${VERSION} && make -j 2 && cd .. && cp ./${NAME}-${VERSION}/${NAME} ./ && rm -rf ./${NAME}-${VERSION}/ && strip ${NAME}

RUN mv /samtools /usr/local/bin/

RUN rm -f ./${NAME} \
  && rm -rf /var/lib/apt/lists/*