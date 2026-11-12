FROM ubuntu:22.04
RUN apt-get update && apt-get install -y --no-install-recommends bind9 dnsutils && rm -rf /var/lib/apt/lists/*
USER bind
CMD ["named", "-g", "-c", "/config/named.conf"]
