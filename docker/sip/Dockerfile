FROM ubuntu:24.04

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends asterisk \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /run/asterisk \
    && chown -R asterisk:asterisk /run/asterisk /var/lib/asterisk /var/log/asterisk /var/spool/asterisk

# Las configuraciones se montan en solo lectura desde compose.
USER asterisk:asterisk

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["asterisk", "-rx", "core show uptime"]

CMD ["asterisk", "-f", "-vvv"]
