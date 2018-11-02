FROM ubuntu:18.04

RUN groupadd -g 5000 blackhole && useradd -d /home/blackhole -m -u 5000 -g 5000 blackhole

RUN DEBIAN_FRONTEND=noninteractive && apt-get update && apt-get dist-upgrade -y && apt-get install -y \
  curl \
  python \
  python3 \
  python-pip \
  python-virtualenv \
  python3-pip \
  sqlite3 \
  wget \
  && rm -rf /var/lib/apt/lists/*

ENV TINI_VERSION v0.18.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini.asc /tini.asc
RUN \
  gpg -v --keyserver ipv4.pool.sks-keyservers.net --recv-keys 595E85A6B1B4779EA4DAAEC70B588DFF0527A9B7 && \
  gpg --verify /tini.asc && \
  chmod +x /tini

RUN mkdir -p /opt/blackholebandicoot/db && chown -R blackhole:blackhole /opt/blackholebandicoot
USER blackhole
COPY --chown=blackhole:blackhole requirements.txt /opt/blackholebandicoot
RUN virtualenv -p python3 /opt/blackholebandicoot/venv && \
    /opt/blackholebandicoot/venv/bin/pip install --no-deps -r /opt/blackholebandicoot/requirements.txt

COPY --chown=blackhole:blackhole config.json /opt/blackholebandicoot
COPY --chown=blackhole:blackhole blackholebandicoot /opt/blackholebandicoot/blackholebandicoot

ENV LANG="en_US.UTF-8" \
    PATH="/opt/blackholebandicoot/venv/bin:$PATH" \
    PYTHONPATH="/opt/blackholebandicoot"

EXPOSE 4000/tcp

WORKDIR /opt/blackholebandicoot

ENTRYPOINT ["/tini", "-e", "143", "--"]
CMD ["gunicorn", "-w", "4", "-k", "gevent", "-b", "0.0.0.0:4000", \
     "--access-logfile", "-", "--error-logfile", "-", "blackholebandicoot.app:app"]
