ARG OH_VERSION=1.7.0
ARG OH_BASE_IMAGE=ghcr.io/openhands/openhands
FROM ${OH_BASE_IMAGE}:${OH_VERSION}

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    coreutils jq ripgrep fd-find sqlite3 moreutils ca-certificates curl xz-utils \
    && arch="$(dpkg --print-architecture)" \
    && case "$arch" in amd64) wx_arch=x86_64-unknown-linux-musl ;; arm64) wx_arch=aarch64-unknown-linux-musl ;; *) echo "unsupported arch $arch"; exit 1 ;; esac \
    && curl -fsSL "https://github.com/watchexec/watchexec/releases/download/v2.3.2/watchexec-2.3.2-${wx_arch}.tar.xz" -o /tmp/watchexec.tar.xz \
    && tar -xJf /tmp/watchexec.tar.xz -C /tmp \
    && install -m 0755 /tmp/watchexec-2.3.2-${wx_arch}/watchexec /usr/local/bin/watchexec \
    && rm -rf /tmp/watchexec* /var/lib/apt/lists/* \
    && ln -sf "$(which fdfind)" /usr/local/bin/fd

RUN mkdir -p /opt/oh-pro/skills /opt/oh-pro/scripts /opt/oh-pro/hooks \
             /opt/oh-pro/templates /opt/oh-pro/patches /.openhands-state/swd

COPY patches/ /opt/oh-pro/patches/

ENV PYTHONPATH=/opt/oh-pro/patches:${PYTHONPATH}

COPY scripts/healthcheck.sh /usr/local/bin/oh-healthcheck
RUN chmod +x /usr/local/bin/oh-healthcheck

LABEL oh.pro.version="1.0.1" \
      oh.base.version="1.7.0" \
      maintainer="oh-pro"
